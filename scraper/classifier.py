import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

def classify_with_gpt(bio):
    """
    Use OpenAI GPT to classify Instagram profile bio into business types.
    Returns one of ['Retailer', 'Reseller', 'Distributor', 'Repair Shop', 'Unknown'].
    """
    prompt = f"""
You are a helpful assistant that classifies cellphone business types based on Instagram bio text.

Bio:
\"\"\"{bio}\"\"\"

Classify this bio into one of these categories:
- Retailer
- Reseller
- Distributor
- Repair Shop
- Unknown (if none apply)

Only respond with one word from the list above.
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        classification = response.choices[0].message.content.strip()
        if classification in ["Retailer", "Reseller", "Distributor", "Repair Shop", "Unknown"]:
            return classification
        else:
            return "Unknown"
    except Exception as e:
        print(f"GPT classification failed: {e}")
        return "Unknown"


def classify_profile(bio, use_gpt=False):
    """
    Classify Instagram profile type based on bio keywords, optionally using GPT.

    Args:
        bio (str): Profile bio text
        use_gpt (bool): Whether to fallback to GPT classification if keyword classification fails

    Returns:
        str: One of ['Retailer', 'Reseller', 'Distributor', 'Repair Shop', 'Unknown']
    """

    bio_lower = bio.lower()

    if any(word in bio_lower for word in ["venta", "mayoreo", "distribuidor", "distribución", "distribuidora"]):
        return "Distributor"
    elif any(word in bio_lower for word in ["reparación", "servicio", "desbloqueo", "repair", "unlock", "service"]):
        return "Repair Shop"
    elif any(word in bio_lower for word in ["revendedor", "reseller", "reventa", "flipping"]):
        return "Reseller"
    elif any(word in bio_lower for word in ["iphone", "samsung", "celulares", "accesorios", "venta directa", "retail"]):
        return "Retailer"
    else:
        if use_gpt:
            return classify_with_gpt(bio)
        else:
            return "Unknown"

def classify_profile(profile):
    """
    Classify the profile based on simple heuristics or keywords.

    Args:
        profile (dict): The profile data.

    Returns:
        str: The classification label (e.g., 'business', 'influencer', 'personal').
    """
    bio = profile.get('bio', '').lower()

    if 'shop' in bio or 'store' in bio:
        return 'business'
    elif 'blogger' in bio or 'influencer' in bio:
        return 'influencer'
    else:
        return 'personal'
