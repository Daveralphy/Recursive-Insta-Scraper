import instaloader

def scrape_followers_and_following(seed_usernames, limit=500):
    """
    Scrape followers and following lists from given seed Instagram usernames.

    Args:
        seed_usernames (list): List of Instagram usernames to start scraping from.
        limit (int): Maximum number of followers/following to scrape per seed user.

    Returns:
        list: Unique list of usernames scraped.
    """
    L = instaloader.Instaloader()
    all_usernames = set()

    for seed in seed_usernames:
        try:
            profile = instaloader.Profile.from_username(L.context, seed)
            
            # Scrape followers
            count = 0
            for follower in profile.get_followers():
                all_usernames.add(follower.username)
                count += 1
                if limit and count >= limit:
                    break

            # Scrape following
            count = 0
            for followee in profile.get_followees():
                all_usernames.add(followee.username)
                count += 1
                if limit and count >= limit:
                    break
                
        except Exception as e:
            print(f"Error scraping {seed}: {e}")

    return list(all_usernames)
