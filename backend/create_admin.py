#!/usr/bin/env python3
"""
Create an admin user in Neo4j.
Run inside the backend container:
  docker compose exec backend python create_admin.py
"""
import os
import sys
from datetime import datetime, timezone

import bcrypt
from neo4j import GraphDatabase


def main() -> None:
    name = input("Name: ").strip()
    email = input("Email: ").strip()
    password = input("Password: ").strip()

    if not (name and email and password):
        print("All fields are required.")
        sys.exit(1)

    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
    )

    with driver.session() as session:
        existing = session.run(
            "MATCH (u:User {email: $email}) RETURN u", email=email
        ).single()
        if existing:
            print(f"User {email} already exists.")
            sys.exit(1)

        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        session.run(
            """
            CREATE (u:User {
                name: $name, email: $email, role: 'admin',
                password_hash: $ph, created_at: $ts
            })
            """,
            name=name,
            email=email,
            ph=password_hash,
            ts=datetime.now(timezone.utc).isoformat(),
        )
        print(f"Admin '{email}' created.")


if __name__ == "__main__":
    main()
