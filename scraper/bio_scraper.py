from instagrapi import Client
import time
import random

# Spanish and Portuguese keywords related to cellphone businesses
KEYWORDS = [
    "celular", "telefono", "móvil", "movil", "smartphone", "accesorios",
    "venta", "reparacion", "reparação", "conserto", "loja", "distribuidor",
    "revendedor", "venda", "atacado", "varejo", "assistência", "telemovel", 
    "contact", "email", "whatsapp", "phone", "instagram"
]

def contains_keywords(text):
    """
    Checks if the given text contains any of the predefined keywords.
    
    Args:
        text (str): Text to search for keywords.

    Returns:
        bool: True if any keyword is found, False otherwise.
    """
    if not text:
        return False
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in KEYWORDS)

def scrape_bio_data(usernames, client: Client, delay_min=1, delay_max=3):
    """
    Performs a light scrape of user profiles to retrieve username, full name, and bio,
    and filters out profiles that do not contain relevant keywords.

    Args:
        usernames (list): List of Instagram usernames.
        client (Client): Authenticated Instagrapi client.
        delay_min (int): Minimum delay between requests.
        delay_max (int): Maximum delay between requests.

    Returns:
        list of dict: Filtered list of profile info dictionaries.
    """
    bio_data = []

    for username in usernames:
        try:
            user_info = client.user_info_by_username(username)
            profile = {
                "username": username,
                "full_name": user_info.full_name,
                "bio": user_info.biography
            }
            
            if contains_keywords(user_info.full_name) or contains_keywords(user_info.biography):
                bio_data.append(profile)
                print(f"Relevant bio found: {username}")
            else:
                print(f"Irrelevant profile skipped: {username}")

            time.sleep(random.uniform(delay_min, delay_max))

        except Exception as e:
            print(f"Failed to scrape bio for {username}: {e}")

    return bio_data
