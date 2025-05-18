import re
import instaloader

WHATSAPP_NUMBER_REGEX = re.compile(
    r"(\+?\d{1,3}[-.\s]?)?(\(?\d{1,4}\)?[-.\s]?)?(\d{3,4}[-.\s]?){2,5}"
)
WHATSAPP_LINK_REGEX = re.compile(r"(https?://)?chat\.whatsapp\.com/[a-zA-Z0-9]+")

def extract_whatsapp_number(text):
    matches = WHATSAPP_NUMBER_REGEX.findall(text)
    if matches:
        # Return the first full match as a concatenated string
        for match in matches:
            combined = "".join(match).strip()
            if combined:
                return combined
    return None

def extract_whatsapp_group_link(text):
    match = WHATSAPP_LINK_REGEX.search(text)
    return match.group(0) if match else None

def scrape_full_profile(usernames):
    """
    Scrape full profile info including WhatsApp detection.

    Args:
        usernames (list): List of usernames filtered from bio_scraper.py

    Returns:
        dict: username -> dict with profile fields + WhatsApp number/group link
    """
    L = instaloader.Instaloader()
    profiles = {}

    for username in usernames:
        try:
            profile = instaloader.Profile.from_username(L.context, username)

            bio = profile.biography or ""
            full_name = profile.full_name or ""
            external_url = profile.external_url or ""
            follower_count = profile.followers
            profile_url = f"https://instagram.com/{username}"

            whatsapp_number = extract_whatsapp_number(bio + " " + external_url)
            whatsapp_group = extract_whatsapp_group_link(bio + " " + external_url)

            profiles[username] = {
                "username": username,
                "full_name": full_name,
                "bio": bio,
                "external_url": external_url,
                "follower_count": follower_count,
                "profile_url": profile_url,
                "whatsapp_number": whatsapp_number,
                "whatsapp_group_link": whatsapp_group,
            }
        except Exception as e:
            print(f"Error scraping full profile {username}: {e}")

    return profiles

def full_profile_scrape(usernames):
    """
    Placeholder function to simulate full profile scraping for given Instagram usernames.

    Args:
        usernames (list): List of usernames.

    Returns:
        list: Dictionary of profiles with extracted metadata.
    """
    profiles = []
    for username in usernames:
        profile_data = {
            "username": username,
            "followers": 1000,  # Simulated value
            "following": 150,   # Simulated value
            "bio": "Sample bio with WhatsApp",
            "posts": 35         # Simulated value
        }
        profiles.append(profile_data)
    return profiles

