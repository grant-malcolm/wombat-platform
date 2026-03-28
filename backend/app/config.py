from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://wombat:wombat@db:5432/wombat"
    media_dir: str = "/app/media"

    model_config = {"env_file": ".env"}


settings = Settings()
