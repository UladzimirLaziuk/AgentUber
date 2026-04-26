import os
from datetime import datetime, timezone
from neo4j import GraphDatabase

_driver = None


def get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            os.environ["NEO4J_URI"],
            auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
        )
    return _driver


def save_user(name: str, email: str, role: str) -> None:
    with get_driver().session() as session:
        session.run(
            "CREATE (u:User {name: $name, email: $email, role: $role, created_at: $ts})",
            name=name,
            email=email,
            role=role,
            ts=datetime.now(timezone.utc).isoformat(),
        )
