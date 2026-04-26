import os
from celery import Celery
from db import save_user

celery = Celery(
    "tasks",
    broker=os.environ.get("REDIS_URL", "redis://redis:6379/0"),
    backend=os.environ.get("REDIS_URL", "redis://redis:6379/0"),
)


@celery.task
def register_user(name: str, email: str, role: str, note: str = "") -> None:
    save_user(name, email, role, note)