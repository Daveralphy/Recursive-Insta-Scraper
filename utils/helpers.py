import time
import logging
import random
import random
import yaml

def setup_logger(name, level=logging.INFO):
    """Create and return a logger with a specified name and level."""
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger

def rate_limit_delay(min_delay=1, max_delay=3):
    """
    Sleep for a random amount of time between min_delay and max_delay seconds
    to mimic human-like behavior and avoid being rate limited.
    """
    delay = random.uniform(min_delay, max_delay)
    time.sleep(delay)

def deduplicate_list(items):
    """
    Return a list with duplicates removed while preserving original order.
    """
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result

def normalize_username(username):
    """
    Clean and normalize Instagram usernames (strip @, lowercase, etc.)
    """
    if username.startswith('@'):
        username = username[1:]
    return username.lower().strip()


def rotate_proxy(proxies):
    """
    Randomly rotate proxies from a given list.

    Args:
        proxies (list): List of proxy strings.

    Returns:
        str: A selected proxy string.
    """
    if not proxies:
        return None
    return random.choice(proxies)

def rate_limit_delay(min_delay=2, max_delay=5):
    """
    Sleep for a random time interval to simulate human behavior and avoid rate limits.

    Args:
        min_delay (int): Minimum seconds to wait.
        max_delay (int): Maximum seconds to wait.
    """
    delay = random.uniform(min_delay, max_delay)
    time.sleep(delay)

def load_config(path="config.yaml"):
    try:
        with open(path, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
            if not config:
                raise ValueError("Config file is empty or not parsed correctly.")
            return config
    except Exception as e:
        logging.error(f"Unexpected error loading config: {e}")
        return None

def setup_logging():
    """
    Set up logging configuration.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
