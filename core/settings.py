# Fetch settings from env and keep available as a settings object
from betterconf import betterconf, DotenvProvider

@betterconf(provider=DotenvProvider(auto_load=True))
class _EnvSettings:
    API_BASE: str
    API_KEY: str
    MODEL_ID: str
    MAX_RETRY: int = 2
    LOG_LEVEL: str = "INFO"

class Settings:
    def __init__(
        self,
        api_base: str = None,
        api_key: str = None,
        model_id: str = None,
        max_retry: int = None,
        log_level: str = None
    ):
        env = _EnvSettings()
        self.API_BASE = api_base or env.API_BASE
        self.API_KEY = api_key or env.API_KEY
        self.MODEL_ID = model_id or env.MODEL_ID
        self.MAX_RETRY = max_retry if max_retry is not None else env.MAX_RETRY
        self.LOG_LEVEL = log_level or env.LOG_LEVEL

default_settings = Settings()
