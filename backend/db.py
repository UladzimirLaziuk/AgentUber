import os
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


def get_user_by_email(email: str) -> dict | None:
    with get_driver().session() as session:
        result = session.run(
            "MATCH (u:User {email: $email}) RETURN u",
            email=email,
        )
        record = result.single()
        return dict(record["u"]) if record else None


def get_all_users() -> list[dict]:
    with get_driver().session() as session:
        result = session.run(
            "MATCH (u:User) RETURN u ORDER BY u.created_at DESC"
        )
        return [dict(r["u"]) for r in result]
