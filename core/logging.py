import logging

from core.settings import default_settings, Settings

# Default configuration on import
logging.basicConfig(level=default_settings.LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')

def configure_logging(settings: Settings):
    """Update the root logger level based on a specific settings object."""
    logging.getLogger().setLevel(settings.LOG_LEVEL)