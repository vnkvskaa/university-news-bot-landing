import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_ids: set[int]
    database_path: str


def load_settings() -> Settings:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN is required. Put it into bot/.env or environment variables.")

    raw_admin_ids = os.getenv("ADMIN_IDS", "").strip()
    admin_ids = {
        int(item)
        for item in raw_admin_ids.split(",")
        if item.strip().isdigit()
    }

    return Settings(
        bot_token=token,
        admin_ids=admin_ids,
        database_path=os.getenv("DATABASE_PATH", "bot.db"),
    )
