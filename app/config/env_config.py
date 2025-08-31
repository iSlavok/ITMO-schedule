import os

from pydantic import BaseModel


class EnvConfig(BaseModel):
    DB_DRIVER: str = os.getenv("DB_DRIVER")
    DB_HOST: str = os.getenv("DB_HOST")
    DB_PORT: int = int(os.getenv("DB_PORT"))
    DB_NAME: str = os.getenv("DB_NAME")
    DB_USER: str = os.getenv("DB_USER")
    DB_PASS: str = os.getenv("DB_PASS")
    REDIS_HOST: str = os.getenv("REDIS_HOST")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT"))
    BOT_TOKEN: str = os.getenv("BOT_TOKEN")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")


env_config = EnvConfig()
