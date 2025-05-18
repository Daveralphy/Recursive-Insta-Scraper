import time
import random
import os
from dotenv import load_dotenv
from scraper.followers_scraper import scrape_followers_and_following
from scraper.bio_scraper import light_bio_scrape_and_filter
from scraper.profile_scraper import full_profile_scrape
from scraper.whatsapp_detector import detect_whatsapp_info
from scraper.classifier import classify_profile
from scraper.exporter import export_results
from utils.helpers import load_config, setup_logging

def main():
    config = load_config("config.yaml")
    setup_logging()

    # Load Instagram credentials from .env file
    load_dotenv("logincredentials.txt")
    insta_username = os.getenv("INSTAGRAM_USERNAME")
    insta_password = os.getenv("INSTAGRAM_PASSWORD")

    # Access nested config sections
    scrape_cfg = config.get("scrape", {})
    export_cfg = config.get("export", {})

    seed_usernames = scrape_cfg.get("seed_usernames", [])
    limit = scrape_cfg.get("limit", 500)
    delay_min = scrape_cfg.get("delay_min", 1)
    delay_max = scrape_cfg.get("delay_max", 3)
    recursion = scrape_cfg.get("recursion", False)
    export_path = export_cfg.get("output_path", "output/results.csv")
    export_format = export_cfg.get("format", "csv").lower()

    # Validate export format
    if export_format not in ("csv", "excel"):
        raise ValueError("Unsupported export format. Choose 'excel' or 'csv'.")

    # Step 1 & 2: Scrape followers and following from seed users
    all_usernames = scrape_followers_and_following(seed_usernames, limit)
    unique_usernames = list(set(all_usernames))

    # Step 3: Light bio scrape + filter
    filtered_usernames = []
    for username in unique_usernames:
        bio_data = light_bio_scrape_and_filter(username)
        if bio_data:
            filtered_usernames.append(username)
        time.sleep(random.uniform(delay_min, delay_max))

    # Step 4: Full profile scrape + WhatsApp detection
    detailed_profiles = []
    for username in filtered_usernames:
        profile = full_profile_scrape(username)
        if profile:
            profile.update(detect_whatsapp_info(profile))
            detailed_profiles.append(profile)
        time.sleep(random.uniform(delay_min, delay_max))

    # Step 5: Classification
    for profile in detailed_profiles:
        profile["type"] = classify_profile(profile)

    # Step 6: Export results
    export_results(detailed_profiles, export_path, export_format)

    # Step 7: Optional recursion
    if recursion:
        print("Recursion enabled, but recursive logic is not implemented yet.")

if __name__ == "__main__":
    main()
