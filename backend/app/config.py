from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://wombat:wombat@db:5432/wombat"
    media_dir: str = "/app/media"
    active_detector: str = "placeholder"  # "placeholder" | "speciesnet"

    model_config = {"env_file": ".env"}

    @property
    def active_detector_url(self) -> str:
        urls = {
            "placeholder": "http://detector-placeholder:8100",
            "speciesnet": "http://detector-speciesnet:8101",
        }
        return urls.get(self.active_detector, urls["placeholder"])

    def detector_url(self, detector_id: str) -> str:
        urls = {
            "placeholder": "http://detector-placeholder:8100",
            "speciesnet": "http://detector-speciesnet:8101",
        }
        return urls.get(detector_id, urls["placeholder"])


settings = Settings()
