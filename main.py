import time
from scraper.followers_scraper import scrape_followers_and_following
from scraper.bio_scraper import light_bio_scrape_and_filter
from scraper.profile_scraper import full_profile_scrape
from scraper.whatsapp_detector import detect_whatsapp_info
from scraper.classifier import classify_profile
from scraper.exporter import export_results
from utils.helpers import load_config, setup_logging

def main():
    config = load_config("config/config.yaml")
    setup_logging()

    seed_usernames = config.get("seed_usernames", [])
    limit = config.get("limit", 500)
    delay = config.get("delay", 2)
    recursion = config.get("recursion", False)

    # Step 1 & 2: Scrape followers and following from seed users
    all_usernames = scrape_followers_and_following(seed_usernames, limit)

    # Remove duplicates
    unique_usernames = list(set(all_usernames))

    filtered_usernames = []
    # Step 3: Light bio scrape + filter
    for username in unique_usernames:
        bio_data = light_bio_scrape_and_filter(username)
        if bio_data:  # Passed filter
            filtered_usernames.append(username)
        time.sleep(delay)

    detailed_profiles = []
    # Step 4: Full profile scrape + WhatsApp detection
    for username in filtered_usernames:
        profile = full_profile_scrape(username)
        if profile:
            profile.update(detect_whatsapp_info(profile))
            detailed_profiles.append(profile)
        time.sleep(delay)

    # Step 5: Classification
    for profile in detailed_profiles:
        profile["type"] = classify_profile(profile)

    # Step 6: Export results
    export_results(detailed_profiles, config.get("export_path", "output.csv"))

    # Step 7: Optional recursion (re-feed usernames)
    if recursion:
        # You can implement recursive scraping logic here or in a helper
        print("Recursion enabled, implement recursive scraping logic.")

if __name__ == "__main__":
    main()
