import re

# Regex patterns to detect WhatsApp numbers and group links
WHATSAPP_NUMBER_PATTERNS = [
    r'\+?\d{1,4}[\s\-]?\(?\d{1,4}\)?[\s\-]?\d{3,}',  # General international number format with optional country code
    r'wa\.me\/\d+',                                 # wa.me short links
    r'Wsp[:\s]?\+?\d+',                             # Variants with "Wsp" label
]

WHATSAPP_GROUP_LINK_PATTERN = r'(https?:\/\/)?chat\.whatsapp\.com\/[A-Za-z0-9]+'

def extract_whatsapp_numbers(text):
    numbers = set()
    for pattern in WHATSAPP_NUMBER_PATTERNS:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        for match in matches:
            numbers.add(match.strip())
    return list(numbers)

def extract_whatsapp_group_links(text):
    matches = re.findall(WHATSAPP_GROUP_LINK_PATTERN, text, flags=re.IGNORECASE)
    return list(set(matches))

def detect_whatsapp_info(bio_text):
    """
    Returns a dictionary with detected WhatsApp numbers and group links from bio text.
    """
    return {
        "whatsapp_numbers": extract_whatsapp_numbers(bio_text),
        "whatsapp_group_links": extract_whatsapp_group_links(bio_text)
    }

def detect_whatsapp_info(profiles):
    """
    Detect WhatsApp information in user bios or other profile data.

    Args:
        profiles (list): List of profile dictionaries.

    Returns:
        list: Filtered list of profiles that likely contain WhatsApp info.
    """
    whatsapp_keywords = ['whatsapp', 'wa.me', '+', 'contact me on', 'reach me on']
    detected = []

    for profile in profiles:
        bio = profile.get('bio', '').lower()
        if any(keyword in bio for keyword in whatsapp_keywords):
            detected.append(profile)

    return detected

