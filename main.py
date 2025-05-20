# main.py

from selenium import webdriver
from utils.helpers import load_config, setup_logger, deduplicate_usernames
from scrapers.login import LoginHandler
from scrapers.followers_scraper import FollowersScraper
from scrapers.profile_scraper import ProfileScraper
from filters.keyword_filter import is_phone_related
from detectors.whatsapp_detector import extract_whatsapp_info
from classifier.classifier import classify_profile
from exporter.exporter import export_results
import time

def main():
    config = load_config()
    logger = setup_logger()

    driver = webdriver.Chrome()  # You can switch driver here if needed

    login_handler = LoginHandler(driver, config)
    if not login_handler.login():
        logger.error("Login failed. Exiting.")
        driver.quit()
        return

    logger.info("Login successful. Starting scraping...")

    followers_scraper = FollowersScraper(driver, config)
    profile_scraper = ProfileScraper(driver, config)

    seed_usernames = config.get("seed_usernames", [])
    if not seed_usernames:
        logger.error("No seed usernames found in config. Exiting.")
        driver.quit()
        return

    recursion_enabled = config.get("enable_recursion", True)
    max_profiles = config.get("max_profiles", 500)
    delay = config.get("delay_between_requests", 2)

    to_process = set(seed_usernames)
    processed = set()
    results = []

    while to_process and len(processed) < max_profiles:
        current_username = to_process.pop()
        if current_username in processed:
            continue

        # --- NEW: Scrape seed username profile first ---
        logger.info(f"Scraping seed profile first: {current_username}")
        profile_data = profile_scraper.search_and_scrape_profile(current_username)
        if profile_data:
            if is_phone_related(profile_data):
                whatsapp_number, whatsapp_group = extract_whatsapp_info(profile_data)
                account_type = classify_profile(profile_data)

                result = {
                    "Username": current_username,
                    "Full Name": profile_data.get("full_name", ""),
                    "Bio": profile_data.get("bio", ""),
                    "WhatsApp Number": whatsapp_number,
                    "WhatsApp Group Link": whatsapp_group,
                    "Type": account_type,
                    "Region": profile_data.get("region", ""),
                    "Follower Count": profile_data.get("follower_count", 0),
                    "Profile URL": profile_data.get("profile_url", f"https://instagram.com/{current_username}"),
                    "External Link": profile_data.get("external_link", "")
                }
                results.append(result)
                logger.info(f"Saved seed profile: {current_username}")

                if recursion_enabled:
                    to_process.add(current_username)

                if len(results) >= max_profiles:
                    logger.info("Reached profile limit after seed profile scrape. Exiting loop.")
                    break
            else:
                logger.info(f"Seed profile filtered out (not phone related): {current_username}")
        else:
            logger.warning(f"Could not scrape seed profile: {current_username}")

        # --- Then scrape followers/following as before ---
        logger.info(f"Fetching followers/following for: {current_username}")
        try:
            followers = followers_scraper.scrape_followers(current_username)
            following = followers_scraper.scrape_following(current_username)
        except Exception as e:
            logger.warning(f"Failed scraping followers/following of {current_username}: {str(e)}")
            processed.add(current_username)
            continue

        scraped_usernames = followers + following
        logger.info(f"Found {len(scraped_usernames)} accounts from {current_username}")

        for username in scraped_usernames:
            if username in processed:
                continue

            logger.info(f"Processing profile: {username}")
            profile_data = profile_scraper.search_and_scrape_profile(username)
            if not profile_data:
                logger.warning(f"Could not scrape profile for {username}. Skipping.")
                continue

            if not is_phone_related(profile_data):
                logger.info(f"Filtered out: {username} — Not phone related.")
                continue

            whatsapp_number, whatsapp_group = extract_whatsapp_info(profile_data)
            account_type = classify_profile(profile_data)

            result = {
                "Username": username,
                "Full Name": profile_data.get("full_name", ""),
                "Bio": profile_data.get("bio", ""),
                "WhatsApp Number": whatsapp_number,
                "WhatsApp Group Link": whatsapp_group,
                "Type": account_type,
                "Region": profile_data.get("region", ""),
                "Follower Count": profile_data.get("follower_count", 0),
                "Profile URL": profile_data.get("profile_url", f"https://instagram.com/{username}"),
                "External Link": profile_data.get("external_link", "")
            }

            results.append(result)
            logger.info(f"Saved: {username}")

            if recursion_enabled:
                to_process.add(username)

            if len(results) >= max_profiles:
                logger.info("Reached profile limit. Exiting loop.")
                break

            if delay:
                time.sleep(delay)

        processed.add(current_username)

    export_filename = config.get("export_filename", "results.csv")
    export_results(results, export_filename)
    logger.info(f"Export complete. {len(results)} profiles saved to {export_filename}")

    driver.quit()

if __name__ == "__main__":
    main()
