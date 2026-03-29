from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://wombat:wombat@db:5432/wombat"
    media_dir: str = "/app/media"
    active_detector: str = "placeholder"  # "placeholder" | "speciesnet" | "megadetector" | "awc135"
    megadetector_url: str = "http://detector-megadetector:8102"

    model_config = {"env_file": ".env"}

    @property
    def active_detector_url(self) -> str:
        return self.detector_url(self.active_detector)

    def detector_url(self, detector_id: str) -> str:
        urls = {
            "placeholder": "http://detector-placeholder:8100",
            "speciesnet": "http://detector-speciesnet:8101",
            "megadetector": self.megadetector_url,
            "awc135": "http://detector-awc135:8103",
        }
        return urls.get(detector_id, urls["placeholder"])


settings = Settings()
