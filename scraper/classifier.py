# classifier.py

def classify_profile(profile):
    """
    Classifies the profile into a business type based on keywords found in the bio or full name.

    Args:
        profile (dict): A dictionary with keys like 'bio' and 'full_name'.

    Returns:
        str: One of ['Retailer', 'Reseller', 'Distributor', 'Repair Shop', 'Unknown'].
    """
    bio = profile.get('bio', '').lower()
    name = profile.get('full_name', '').lower()

    text = f"{name} {bio}"

    if any(word in text for word in ['reparacion', 'reparação', 'conserto', 'assistência']):
        return "Repair Shop"
    elif any(word in text for word in ['distribuidor', 'atacado']):
        return "Distributor"
    elif any(word in text for word in ['revendedor', 'reseller']):
        return "Reseller"
    elif any(word in text for word in ['loja', 'tienda', 'retail', 'varejo', 'venta']):
        return "Retailer"
    else:
        return "Unknown"
