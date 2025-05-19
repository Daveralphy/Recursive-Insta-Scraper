import yaml
import time
import random
import logging

def load_config(filepath="config.yaml"):
    """
    Load configuration from a YAML file.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config

def random_delay(min_seconds=1, max_seconds=3):
    """
    Sleep for a random amount of time between min_seconds and max_seconds.
    """
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)

def safe_get(dct, *keys, default=None):
    """
    Safely get nested dictionary keys.
    Example: safe_get(data, 'key1', 'key2', default='N/A')
    """
    for key in keys:
        if not isinstance(dct, dict) or key not in dct:
            return default
        dct = dct[key]
    return dct

def setup_logger(name="latam_scraper", level=logging.INFO):
    """
    Sets up and returns a logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        logger.setLevel(level)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def select_proxy(proxies):
    """
    Select a proxy from the proxy list randomly.
    Return None if list is empty.
    """
    if proxies:
        return random.choice(proxies)
    return None
