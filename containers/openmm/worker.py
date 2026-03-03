import os
from celery import Celery

redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")

app = Celery("totalSimulation", broker=redis_url, backend=redis_url)

app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    result_expires=3600,
)

# Import tasks
import openmm_tool  # noqa: F401
