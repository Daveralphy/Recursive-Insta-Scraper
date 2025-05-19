# profile_scraper.py

from instagrapi import Client
import time
import random

def scrape_full_profiles(filtered_users, client: Client, delay_min=1, delay_max=3):
    """
    Scrapes full profile details for users already filtered through bio scraping.

    Args:
        filtered_users (list of dict): List of filtered users with 'username', 'full_name', and 'bio'.
        client (Client): Authenticated Instagrapi client.
        delay_min (int): Minimum delay between requests.
        delay_max (int): Maximum delay between requests.

    Returns:
        list of dict: Detailed profile data for export.
    """
    full_profiles = []

    for user in filtered_users:
        username = user['username']
        try:
            user_info = client.user_info_by_username(username)

            profile_data = {
                "username": username,
                "full_name": user_info.full_name,
                "bio": user_info.biography,
                "follower_count": user_info.follower_count,
                "profile_url": f"https://instagram.com/{username}",
                "external_url": user_info.external_url or ""
            }

            full_profiles.append(profile_data)
            print(f"Full profile scraped: {username}")
            time.sleep(random.uniform(delay_min, delay_max))

        except Exception as e:
            print(f"Failed to scrape full profile for {username}: {e}")

    return full_profiles
