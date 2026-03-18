"""On-demand worker container lifecycle manager.

Uses Docker SDK to start/stop worker containers via the mounted Docker socket.
Embedded tools (rebound, qutip, etc.) run inside the orchestrator — no container ops needed.
"""

import asyncio
import logging
import subprocess
import time
from functools import lru_cache

import docker

logger = logging.getLogger(__name__)

# Tool key → docker-compose service name for containerized workers.
# Tools NOT listed here are embedded in the orchestrator and need no container management.
TOOL_CONTAINER_MAP: dict[str, str] = {
    "openmm": "openmm-worker",
    "psi4": "psi4-worker",
    "gromacs": "gromacs-worker",
    "namd": "namd-worker",
    "qmmm": "qmmm-worker",
    "fenics": "fenics-worker",
    "elmer": "elmer-worker",
    "nest": "nest-worker",
    "qe": "qe-worker",
    "sagemath": "sagemath-worker",
    "manim": "manim-worker",
    "su2": "su2-worker",
    "firedrake": "firedrake-worker",
    "openfoam": "openfoam-worker",
    "dedalus": "dedalus-worker",
    "einstein_toolkit": "einstein-toolkit-worker",
    "slim": "slim-worker",
    "vtk": "vtk-worker",
    "meep": "meep-worker",
}

COMPOSE_PROJECT = "totalsimulation"
IDLE_TIMEOUT = 300  # 5 minutes
REAPER_INTERVAL = 60  # check every 60s
CELERY_READY_TIMEOUT = 120  # max wait for celery worker registration


class WorkerContainerNotFound(Exception):
    """Raised when a worker container doesn't exist (not even stopped)."""


class DockerManager:
    def __init__(self):
        self._client: docker.DockerClient | None = None
        self._locks: dict[str, asyncio.Lock] = {}
        self._last_activity: dict[str, float] = {}
        self._reaper_task: asyncio.Task | None = None

    @property
    def client(self) -> docker.DockerClient:
        if self._client is None:
            self._client = docker.from_env()
        return self._client

    def _get_lock(self, service_name: str) -> asyncio.Lock:
        if service_name not in self._locks:
            self._locks[service_name] = asyncio.Lock()
        return self._locks[service_name]

    def get_service_for_tool(self, tool_key: str) -> str | None:
        """Return the compose service name for a tool, or None if embedded."""
        return TOOL_CONTAINER_MAP.get(tool_key)

    def _find_container(self, service_name: str):
        """Find a container by its compose service label."""
        containers = self.client.containers.list(
            all=True,
            filters={
                "label": [
                    f"com.docker.compose.service={service_name}",
                    f"com.docker.compose.project={COMPOSE_PROJECT}",
                ],
            },
        )
        return containers[0] if containers else None

    def is_container_running(self, service_name: str) -> bool:
        """Check if a container is currently running."""
        container = self._find_container(service_name)
        return container is not None and container.status == "running"

    async def ensure_worker(self, tool_key: str) -> dict:
        """Ensure the worker container for a tool is running.

        Returns:
            {"needed": False} if tool is embedded (no container needed)
            {"needed": True, "started": False} if already running
            {"needed": True, "started": True, "service": ...} if just started
        """
        service_name = self.get_service_for_tool(tool_key)
        if service_name is None:
            return {"needed": False}

        lock = self._get_lock(service_name)
        async with lock:
            container = self._find_container(service_name)

            if container is None:
                raise WorkerContainerNotFound(
                    f"Container for service '{service_name}' not found. "
                    f"Run './scripts/build.sh' to build and create containers."
                )

            if container.status == "running":
                self.record_activity(tool_key)
                return {"needed": True, "started": False, "service": service_name}

            # Start the stopped container
            logger.info("Starting worker container: %s", service_name)
            await asyncio.to_thread(container.start)

            # Wait for Celery worker to register
            await self._wait_for_celery_ready(service_name)

            self.record_activity(tool_key)
            logger.info("Worker container ready: %s", service_name)
            return {"needed": True, "started": True, "service": service_name}

    async def build_worker(self, tool_key: str) -> dict:
        """Build the Docker image and create a stopped container for a worker.

        Uses docker compose CLI (requires /project mount and docker binary).
        """
        service_name = self.get_service_for_tool(tool_key)
        if service_name is None:
            return {"needed": False}

        compose_file = "/project/docker-compose.yml"
        compose_base = [
            "docker", "compose",
            "-f", compose_file,
            "--project-directory", "/project",
            "-p", COMPOSE_PROJECT,
        ]
        lock = self._get_lock(f"build-{service_name}")
        async with lock:
            logger.info("Building worker image: %s", service_name)
            result = await asyncio.to_thread(
                subprocess.run,
                [*compose_base, "build", service_name],
                capture_output=True, text=True, timeout=1800,
            )
            if result.returncode != 0:
                logger.error("Build failed for %s: %s", service_name, result.stderr[-500:])
                raise RuntimeError(f"Build failed for {service_name}: {result.stderr[-500:]}")

            logger.info("Creating worker container: %s", service_name)
            result = await asyncio.to_thread(
                subprocess.run,
                [*compose_base, "--profile", "workers",
                 "create", "--no-build", service_name],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode != 0:
                logger.error("Create failed for %s: %s", service_name, result.stderr[-500:])
                raise RuntimeError(f"Container create failed for {service_name}: {result.stderr[-500:]}")

            logger.info("Worker built and created: %s", service_name)
            return {"needed": True, "built": True, "service": service_name}

    async def _wait_for_celery_ready(self, service_name: str):
        """Poll celery inspect to confirm the worker has registered its queues."""
        from celery_app import app as celery_app

        deadline = time.monotonic() + CELERY_READY_TIMEOUT
        while time.monotonic() < deadline:
            try:
                result = await asyncio.to_thread(
                    celery_app.control.inspect().active_queues
                )
                if result:
                    # Check if any worker's hostname contains the service name
                    for worker_name in result:
                        if service_name.replace("-", "") in worker_name.replace("-", ""):
                            return
            except Exception:
                pass
            await asyncio.sleep(2)

        logger.warning(
            "Celery worker for %s did not register within %ds — proceeding anyway",
            service_name, CELERY_READY_TIMEOUT,
        )

    async def stop_worker(self, service_name: str) -> bool:
        """Gracefully stop a worker container."""
        lock = self._get_lock(service_name)
        async with lock:
            container = self._find_container(service_name)
            if container is None or container.status != "running":
                return False
            logger.info("Stopping worker container: %s", service_name)
            await asyncio.to_thread(container.stop, timeout=30)
            return True

    def record_activity(self, tool_key: str):
        """Record that a tool was used (resets idle timer)."""
        service_name = self.get_service_for_tool(tool_key)
        if service_name:
            self._last_activity[service_name] = time.monotonic()

    async def _has_active_tasks(self, service_name: str) -> bool:
        """Check if a worker has active Celery tasks."""
        from celery_app import app as celery_app

        try:
            result = await asyncio.to_thread(
                celery_app.control.inspect().active
            )
            if not result:
                return False
            for worker_name, tasks in result.items():
                if service_name.replace("-", "") in worker_name.replace("-", ""):
                    if tasks:
                        return True
        except Exception:
            pass
        return False

    async def _idle_reaper(self):
        """Background task that stops idle worker containers."""
        logger.info("Idle reaper started (timeout=%ds, interval=%ds)", IDLE_TIMEOUT, REAPER_INTERVAL)
        while True:
            try:
                await asyncio.sleep(REAPER_INTERVAL)
                now = time.monotonic()
                for tool_key, service_name in TOOL_CONTAINER_MAP.items():
                    last = self._last_activity.get(service_name)
                    if last is None:
                        continue
                    if now - last < IDLE_TIMEOUT:
                        continue
                    if not self.is_container_running(service_name):
                        continue
                    if await self._has_active_tasks(service_name):
                        # Reset activity since it's still working
                        self._last_activity[service_name] = now
                        continue
                    logger.info("Stopping idle worker: %s (idle %.0fs)", service_name, now - last)
                    await self.stop_worker(service_name)
                    del self._last_activity[service_name]
            except asyncio.CancelledError:
                logger.info("Idle reaper stopped")
                return
            except Exception:
                logger.exception("Error in idle reaper")

    def start_reaper(self):
        """Start the idle reaper background task."""
        if self._reaper_task is None or self._reaper_task.done():
            self._reaper_task = asyncio.create_task(self._idle_reaper())

    def stop_reaper(self):
        """Cancel the idle reaper."""
        if self._reaper_task and not self._reaper_task.done():
            self._reaper_task.cancel()

    def get_worker_status(self) -> list[dict]:
        """Return status of all worker containers."""
        statuses = []
        for tool_key, service_name in TOOL_CONTAINER_MAP.items():
            container = self._find_container(service_name)
            last = self._last_activity.get(service_name)
            image_name = f"{COMPOSE_PROJECT}-{service_name}"
            try:
                self.client.images.get(image_name)
                has_image = True
            except docker.errors.ImageNotFound:
                has_image = False
            except Exception:
                has_image = False
            statuses.append({
                "tool_key": tool_key,
                "service": service_name,
                "status": container.status if container else "not_found",
                "image_exists": has_image,
                "last_activity": last,
                "idle_seconds": (time.monotonic() - last) if last else None,
            })
        return statuses


# Module-level singleton
docker_mgr = DockerManager()
