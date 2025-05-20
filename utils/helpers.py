# utils/helpers.py

import time
import yaml
import logging

def load_config(path="config/config.yaml"):
    """
    Loads configuration settings from the YAML file.
    """
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def delay(seconds):
    """
    Pauses execution for a specified number of seconds.
    """
    time.sleep(seconds)


def remove_duplicates(usernames):
    """
    Removes duplicate usernames from a list.
    """
    return list(set(usernames))


def chunk_list(lst, chunk_size):
    """
    Breaks a list into chunks of a specified size.
    Useful for batch processing.
    """
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


def clean_bio_text(text):
    """
    Cleans up bio text (remove emojis, excess whitespace, etc.)
    """
    if not text:
        return ""
    return text.encode('ascii', 'ignore').decode().strip()

def setup_logger(name="InstagramScraper"):
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger


def deduplicate_usernames(usernames):
    return list(set(usernames))


def load_seed_usernames(seed_file_path):
    try:
        with open(seed_file_path, "r", encoding="utf-8") as f:
            usernames = [line.strip() for line in f if line.strip()]
        return usernames
    except FileNotFoundError:
        return []