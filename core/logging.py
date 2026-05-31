import logging

from core.config import Settings, default_settings

# Default configuration on import
logging.basicConfig(level=default_settings.LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')

def configure_logging(settings: Settings):
    """Update the root logger level based on a specific settings object."""
    logging.getLogger().setLevel(settings.LOG_LEVEL)
