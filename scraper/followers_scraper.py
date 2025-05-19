from instagrapi import Client
import time
import random

def scrape_followers_and_following(client: Client, username, limit=500, delay_min=1, delay_max=3, logger=None):
    collected_usernames = set()
    try:
        try:
            user = client.user_info_by_username(username)
            user_id = user.pk
        except Exception as e:
            msg = f"Failed to get user ID for {username}: {e}"
            if logger: logger.error(msg)
            else: print(msg)
            return []

        msg = f"Scraping followers of {username}..."
        if logger: logger.info(msg)
        else: print(msg)

        followers = client.user_followers(user_id, amount=limit)
        collected_usernames.update([user.username for user in followers.values()])
        time.sleep(random.uniform(delay_min, delay_max))

        msg = f"Scraping following of {username}..."
        if logger: logger.info(msg)
        else: print(msg)

        following = client.user_following(user_id, amount=limit)
        collected_usernames.update([user.username for user in following.values()])
        time.sleep(random.uniform(delay_min, delay_max))

    except Exception as e:
        msg = f"Error scraping {username}: {e}"
        if logger: logger.error(msg)
        else: print(msg)

    return list(collected_usernames)[:limit]
