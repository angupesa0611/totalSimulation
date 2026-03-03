import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from celery.result import AsyncResult
from celery_app import app as celery_app
from auth import validate_ws_token

ws_router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active: dict[str, list[WebSocket]] = {}

    async def connect(self, job_id: str, ws: WebSocket):
        await ws.accept()
        if job_id not in self.active:
            self.active[job_id] = []
        self.active[job_id].append(ws)

    def disconnect(self, job_id: str, ws: WebSocket):
        if job_id in self.active:
            self.active[job_id].remove(ws)
            if not self.active[job_id]:
                del self.active[job_id]

    async def send_update(self, job_id: str, data: dict):
        if job_id in self.active:
            dead = []
            for ws in self.active[job_id]:
                try:
                    await ws.send_json(data)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self.disconnect(job_id, ws)


manager = ConnectionManager()


@ws_router.websocket("/ws/simulation/{job_id}")
async def ws_simulation(ws: WebSocket, job_id: str, token: str = Query(default=None)):
    user = validate_ws_token(token)
    if user is None:
        await ws.close(code=4001)
        return
    await manager.connect(job_id, ws)
    try:
        while True:
            result = AsyncResult(job_id, app=celery_app)
            status = result.status

            update = {"job_id": job_id, "status": status}

            if status == "PROGRESS":
                info = result.info or {}
                update["progress"] = info.get("progress", 0)
                update["message"] = info.get("message", "")
            elif status == "SUCCESS":
                update["result"] = result.result
                await ws.send_json(update)
                break
            elif status == "FAILURE":
                update["message"] = str(result.result)
                await ws.send_json(update)
                break

            await ws.send_json(update)
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(job_id, ws)


@ws_router.websocket("/ws/pipeline/{pipeline_id}")
async def ws_pipeline(ws: WebSocket, pipeline_id: str, token: str = Query(default=None)):
    """WebSocket for pipeline progress — polls pipeline engine."""
    user = validate_ws_token(token)
    if user is None:
        await ws.close(code=4001)
        return
    await ws.accept()
    try:
        while True:
            from pipeline import get_pipeline_status
            status = get_pipeline_status(pipeline_id)

            if status is None:
                await ws.send_json({"pipeline_id": pipeline_id, "status": "NOT_FOUND"})
                break

            await ws.send_json(status)

            if status["status"] in ("SUCCESS", "FAILURE"):
                break

            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass


@ws_router.websocket("/ws/sweep/{sweep_id}")
async def ws_sweep(ws: WebSocket, sweep_id: str, token: str = Query(default=None)):
    """WebSocket for sweep progress — polls sweep engine."""
    user = validate_ws_token(token)
    if user is None:
        await ws.close(code=4001)
        return
    await ws.accept()
    try:
        while True:
            from sweep import get_sweep_status
            status = get_sweep_status(sweep_id)

            if status is None:
                await ws.send_json({"sweep_id": sweep_id, "status": "NOT_FOUND"})
                break

            await ws.send_json(status)

            if status["status"] in ("SUCCESS", "PARTIAL", "FAILURE", "CANCELLED"):
                break

            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass


@ws_router.websocket("/ws/status")
async def ws_global_status(ws: WebSocket, token: str = Query(default=None)):
    """Global status WebSocket — clients send job IDs to track."""
    user = validate_ws_token(token)
    if user is None:
        await ws.close(code=4001)
        return
    await ws.accept()
    tracked_jobs: set[str] = set()

    try:
        while True:
            # Check for new job IDs from client (non-blocking)
            try:
                msg = await asyncio.wait_for(ws.receive_text(), timeout=0.5)
                data = json.loads(msg)
                if data.get("action") == "track":
                    tracked_jobs.add(data["job_id"])
                elif data.get("action") == "untrack":
                    tracked_jobs.discard(data["job_id"])
            except asyncio.TimeoutError:
                pass

            # Send updates for all tracked jobs
            done = set()
            for job_id in tracked_jobs:
                result = AsyncResult(job_id, app=celery_app)
                update = {"job_id": job_id, "status": result.status}
                if result.status == "PROGRESS":
                    info = result.info or {}
                    update["progress"] = info.get("progress", 0)
                    update["message"] = info.get("message", "")
                elif result.status == "SUCCESS":
                    update["result"] = result.result
                    done.add(job_id)
                elif result.status == "FAILURE":
                    update["message"] = str(result.result)
                    done.add(job_id)
                await ws.send_json(update)

            tracked_jobs -= done
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
