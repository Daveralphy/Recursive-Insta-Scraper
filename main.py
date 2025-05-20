from instagrapi import Client
from scraper.followers_scraper import scrape_followers_and_following
from scraper.bio_scraper import scrape_bio_data
from scraper.profile_scraper import scrape_full_profiles
from scraper.whatsapp_detector import detect_whatsapp_info
from scraper.classifier import classify_profile
from scraper.exporter import export_to_csv
from utils.helpers import load_config, random_delay, setup_logger
import time

MAX_RETRIES = 3

def safe_scrape(func, *args, **kwargs):
    """Wrapper to retry scraping functions on failure."""
    logger = kwargs.get('logger')
    retries = 0
    while retries < MAX_RETRIES:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if logger:
                logger.error(f"Error in {func.__name__}: {e}. Retry {retries+1}/{MAX_RETRIES}")
            retries += 1
            time.sleep(2 ** retries)  # exponential backoff
    if logger:
        logger.error(f"Failed to complete {func.__name__} after {MAX_RETRIES} retries.")
    return []

def main():
    logger = setup_logger()
    print("Welcome to Instagram Scraper")

    # Load config
    config = load_config()

    username = input("Enter Instagram username: ")
    password = input("Enter Instagram password: ")

    client = Client()

    # Try loading existing session to avoid repeated logins
    try:
        client.load_settings("session.json")
        # Validate session by getting logged-in user info
        client.user_info(client.user_id)
        logger.info("Loaded existing Instagram session.")
    except Exception:
        # If no valid session, login and save session
        try:
            client.login(username, password)
            client.dump_settings("session.json")
            logger.info("Instagram login successful and session saved.")
        except Exception as e:
            logger.error(f"Login failed: {e}")
            print("Login failed. Check credentials or network.")
            return

    seed_accounts = config.get("seed_usernames", [])
    if not seed_accounts:
        print("No seed accounts found in config. Exiting.")
        return

    all_usernames = set()
    for seed in seed_accounts:
        logger.info(f"Scraping followers and following for seed account: {seed}")
        followers = safe_scrape(
            scrape_followers_and_following,
            client,
            seed,
            limit=config.get("scrape_limit", 500),
            delay_min=config.get("delay_min", 1),
            delay_max=config.get("delay_max", 3),
            logger=logger
        )
        all_usernames.update(followers)
        random_delay(config.get("delay_min", 1), config.get("delay_max", 3))

    logger.info(f"Total usernames collected from seeds: {len(all_usernames)}")

    if not all_usernames:
        logger.info("No usernames found after scraping followers. Exiting.")
        return

    # Light bio scraping + filtering
    bio_data = safe_scrape(
        scrape_bio_data,
        list(all_usernames),
        client,
        delay_min=config.get("delay_min", 1),
        delay_max=config.get("delay_max", 3),
        logger=logger
    )

    logger.info(f"Profiles after keyword/AI filtering: {len(bio_data)}")

    if not bio_data:
        logger.info("No bio data scraped. Exiting.")
        return

    # Full profile scrape
    full_profiles = safe_scrape(
        scrape_full_profiles,
        bio_data,
        client,
        delay_min=config.get("delay_min", 1),
        delay_max=config.get("delay_max", 3),
        logger=logger
    )

    logger.info(f"Full profiles scraped: {len(full_profiles)}")

    if not full_profiles:
        logger.info("No full profiles scraped. Exiting.")
        return

    # Detect WhatsApp info
    profiles_with_whatsapp = detect_whatsapp_info(full_profiles)

    # Classify profiles
    classified_profiles = classify_profile(profiles_with_whatsapp)

    # Export
    if classified_profiles:
        export_to_csv(classified_profiles, filename=config.get("export_filename", "output.csv"))
        logger.info(f"Export completed: {config.get('export_filename', 'results.csv')}")
    else:
        logger.info("No data found to export. Exiting.")

if __name__ == "__main__":
    main()
