import sqlite3
from pathlib import Path
from typing import Optional


class Storage:
    def __init__(self, database_path: str) -> None:
        self.database_path = Path(database_path)
        self.connection = sqlite3.connect(self.database_path)
        self.connection.row_factory = sqlite3.Row

    def setup(self) -> None:
        self.connection.executescript(
            """
            create table if not exists users (
                user_id integer primary key,
                username text,
                full_name text,
                role text,
                goal text,
                created_at text default current_timestamp,
                updated_at text default current_timestamp
            );

            create table if not exists subscriptions (
                user_id integer not null,
                topic_key text not null,
                created_at text default current_timestamp,
                primary key (user_id, topic_key)
            );
            """
        )
        self.connection.commit()

    def upsert_user(self, user_id: int, username: Optional[str], full_name: str) -> None:
        self.connection.execute(
            """
            insert into users (user_id, username, full_name)
            values (?, ?, ?)
            on conflict(user_id) do update set
                username = excluded.username,
                full_name = excluded.full_name,
                updated_at = current_timestamp
            """,
            (user_id, username, full_name),
        )
        self.connection.commit()

    def update_profile(self, user_id: int, role: Optional[str] = None, goal: Optional[str] = None) -> None:
        if role is not None:
            self.connection.execute(
                "update users set role = ?, updated_at = current_timestamp where user_id = ?",
                (role, user_id),
            )
        if goal is not None:
            self.connection.execute(
                "update users set goal = ?, updated_at = current_timestamp where user_id = ?",
                (goal, user_id),
            )
        self.connection.commit()

    def toggle_subscription(self, user_id: int, topic_key: str) -> bool:
        existing = self.connection.execute(
            "select 1 from subscriptions where user_id = ? and topic_key = ?",
            (user_id, topic_key),
        ).fetchone()
        if existing:
            self.connection.execute(
                "delete from subscriptions where user_id = ? and topic_key = ?",
                (user_id, topic_key),
            )
            self.connection.commit()
            return False

        self.connection.execute(
            "insert into subscriptions (user_id, topic_key) values (?, ?)",
            (user_id, topic_key),
        )
        self.connection.commit()
        return True

    def get_subscriptions(self, user_id: int) -> list[str]:
        rows = self.connection.execute(
            "select topic_key from subscriptions where user_id = ? order by created_at",
            (user_id,),
        ).fetchall()
        return [row["topic_key"] for row in rows]

    def get_topic_subscribers(self, topic_key: str) -> list[int]:
        rows = self.connection.execute(
            "select user_id from subscriptions where topic_key = ?",
            (topic_key,),
        ).fetchall()
        return [row["user_id"] for row in rows]

    def count_topic_subscribers(self) -> dict[str, int]:
        rows = self.connection.execute(
            "select topic_key, count(*) as count from subscriptions group by topic_key"
        ).fetchall()
        return {row["topic_key"]: row["count"] for row in rows}
