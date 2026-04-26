import os
from celery import Celery

celery = Celery(
    "tasks",
    broker=os.environ.get("REDIS_URL", "redis://redis:6379/0"),
    backend=os.environ.get("REDIS_URL", "redis://redis:6379/0"),
)


@celery.task
def register_user(name: str, email: str, role: str) -> None:
    from db import save_user
    save_user(name, email, role)
