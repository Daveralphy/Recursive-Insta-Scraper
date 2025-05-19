# whatsapp_detector.py

import re

# Regex for WhatsApp number (international format)
WHATSAPP_NUMBER_REGEX = re.compile(r'\+?\d{1,3}[-.\s]?\(?\d+\)?[-.\s]?\d+[-.\s]?\d+')

# Regex for WhatsApp group links
WHATSAPP_GROUP_REGEX = re.compile(r'https?://chat\.whatsapp\.com/[A-Za-z0-9]+')

def detect_whatsapp_info(profile_data):
    """
    Detects WhatsApp numbers and group links in a user's profile fields.

    Args:
        profile_data (dict): Dictionary containing profile fields like bio and external_url.

    Returns:
        dict: Profile data with 'whatsapp_number' and 'whatsapp_group_link' keys added.
    """
    bio = profile_data.get('bio', '')
    external = profile_data.get('external_url', '')

    combined_text = f"{bio} {external}"

    # Find WhatsApp number
    number_match = WHATSAPP_NUMBER_REGEX.search(combined_text)
    whatsapp_number = number_match.group(0) if number_match else ""

    # Find WhatsApp group link
    group_match = WHATSAPP_GROUP_REGEX.search(combined_text)
    whatsapp_group = group_match.group(0) if group_match else ""

    profile_data['whatsapp_number'] = whatsapp_number
    profile_data['whatsapp_group_link'] = whatsapp_group

    return profile_data
