import instaloader

KEYWORDS = [
    "iphone", "samsung", "venta", "gsm", "celulares", "mayoreo",
    "reparación", "accesorios", "tecnología"
]

def keyword_filter(text):
    text = text.lower()
    return any(keyword in text for keyword in KEYWORDS)

def scrape_light_profile(usernames):
    """
    Scrape bio, name, and external link for each username.
    Filter profiles based on keywords in bio (Spanish/Portuguese focus).

    Args:
        usernames (list): List of Instagram usernames to scrape.

    Returns:
        dict: username -> dict with 'bio', 'name', 'external_url' if passes filter.
    """
    L = instaloader.Instaloader()
    filtered_profiles = {}

    for username in usernames:
        try:
            profile = instaloader.Profile.from_username(L.context, username)
            bio = profile.biography or ""
            name = profile.full_name or ""
            external_url = profile.external_url or ""

            combined_text = f"{bio} {name} {external_url}"

            if keyword_filter(combined_text):
                filtered_profiles[username] = {
                    "bio": bio,
                    "name": name,
                    "external_url": external_url
                }
        except Exception as e:
            print(f"Error scraping profile {username}: {e}")

    return filtered_profiles

def light_bio_scrape_and_filter(usernames):
    """
    Placeholder function to simulate scraping user bios and filtering based on keywords.

    Args:
        usernames (list): List of Instagram usernames.

    Returns:
        list: Filtered list of usernames with desired bio keywords.
    """
    filtered = []
    for username in usernames:
        # Simulated logic for checking keywords in bio
        if "whatsapp" in username.lower() or "contact" in username.lower():
            filtered.append(username)
    return filtered
