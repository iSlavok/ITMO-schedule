from pydantic import SecretStr
from pydantic_settings import BaseSettings


class EnvConfig(BaseSettings):
    DB_DRIVER: str = "postgresql+asyncpg"
    DB_HOST: str = "postgres"
    DB_PORT: int = 5432
    DB_NAME: str = "postgres"
    DB_USER: str = "postgres"
    DB_PASS: SecretStr
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    BOT_TOKEN: SecretStr
    GEMINI_API_KEY: SecretStr


env_config = EnvConfig()
