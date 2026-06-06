from betterconf import DotenvProvider, betterconf


@betterconf(provider=DotenvProvider(auto_load=True))
class _EnvSettings:
    API_BASE: str
    API_KEY: str
    DEFAULT_MODEL: str
    INTENT_MODEL: str = ""
    TOOL_SELECT_MODEL: str = ""
    PARAM_EXTRACT_MODEL: str = ""
    RESPONSE_MODEL: str = ""
    MAX_RETRY: int = 2
    LOG_LEVEL: str = "INFO"


class Settings:
    def __init__(
        self,
        api_base: str = None,
        api_key: str = None,
        default_model: str = None,
        intent_model: str = None,
        tool_select_model: str = None,
        param_extract_model: str = None,
        response_model: str = None,
        max_retry: int = None,
        log_level: str = None,
    ):
        env = _EnvSettings()
        self.API_BASE = api_base or env.API_BASE
        self.API_KEY = api_key or env.API_KEY
        self.DEFAULT_MODEL = default_model or env.DEFAULT_MODEL
        self.INTENT_MODEL = intent_model or env.INTENT_MODEL or self.DEFAULT_MODEL
        self.TOOL_SELECT_MODEL = tool_select_model or env.TOOL_SELECT_MODEL or self.DEFAULT_MODEL
        self.PARAM_EXTRACT_MODEL = param_extract_model or env.PARAM_EXTRACT_MODEL or self.DEFAULT_MODEL
        self.RESPONSE_MODEL = response_model or env.RESPONSE_MODEL or self.DEFAULT_MODEL
        self.MAX_RETRY = max_retry if max_retry is not None else env.MAX_RETRY
        self.LOG_LEVEL = log_level or env.LOG_LEVEL


default_settings = Settings()
