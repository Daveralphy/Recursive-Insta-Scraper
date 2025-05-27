import os
import re
import yaml # NEW: Import yaml to load config

# import openai # Uncomment if you plan to use OpenAI GPT for classification

# Load configuration for keywords
try:
    with open("config.yaml", "r") as config_file:
        config = yaml.safe_load(config_file)
except FileNotFoundError:
    print("Error: config.yaml not found in classifier.py. Using empty keywords.")
    config = {"keywords": []} # Fallback to empty list if config is missing

# Get keywords from config.yaml
CONFIG_KEYWORDS = [k.lower() for k in config.get("keywords", [])]

# Define classification rules.
CLASSIFICATION_RULES = {
    "Retailer": ["venta", "tienda", "local", "compra y venta", "store", "shop", "retail"],
    "Reseller": ["reventa", "oportunidad", "flipping", "mayoreo", "wholesale", "revendedor"],
    "Distributor": ["distribuidor", "mayorista", "suministros", "importador", "distribucion", "provider"],
    "Repair Shop": ["reparacion", "servicio tecnico", "arreglos", "diagnostico", "unlock", "repair", "arregla"],
    "Phone & Accessories": CONFIG_KEYWORDS # Dynamically load keywords from config
}

def classify_profile(profile_data):
    """
    Classifies an Instagram profile based on its bio, full name, and external link.
    Performs bio cleaning, extracts contact information, and applies rule-based classification.
    """
    raw_bio = profile_data.get("Bio", "") # Get the original raw bio
    full_name = profile_data.get("Full Name", "").lower()
    username = profile_data.get("Username", "").lower()
    external_link = profile_data.get("External Link", "").lower()

    # --- NEW: Bio Cleaning Logic ---
    # Strip leading/trailing whitespace and split into lines
    bio_lines = raw_bio.strip().split('\n')
    cleaned_bio_lines = list(bio_lines) # Create a mutable copy to work with

    # Rule 1: If the first line of the bio matches the Full Name, remove it.
    # This prevents duplication if the full name is repeated at the start of the bio.
    if cleaned_bio_lines and full_name and cleaned_bio_lines[0].strip().lower() == full_name:
        cleaned_bio_lines.pop(0) # Remove the first line

    # Rule 2: If the (now) first line of the bio matches the Username (ignoring '@'), remove it.
    # This addresses instances where the username is repeated in the bio's second line.
    if cleaned_bio_lines and username and cleaned_bio_lines[0].strip().lower().replace("@", "") == username:
        cleaned_bio_lines.pop(0) # Remove the (new) first line

    # Reconstruct the bio from the cleaned lines
    cleaned_bio_text = '\n'.join(cleaned_bio_lines).strip()
    profile_data["Bio"] = cleaned_bio_text # Update the 'Bio' field in profile_data with the cleaned version
    # --- END NEW: Bio Cleaning Logic ---

    # Combine relevant text for classification (use the cleaned bio for this)
    text_to_classify = f"{cleaned_bio_text.lower()} {full_name} {external_link}"
    
    classification = "Other" # Default classification

    # Rule-based classification
    # Prioritize more specific classifications if keywords overlap
    priority_categories = ["Repair Shop", "Distributor", "Reseller", "Retailer", "Phone & Accessories"]

    for category in priority_categories:
        keywords = CLASSIFICATION_RULES.get(category, [])
        if any(keyword in text_to_classify for keyword in keywords):
            classification = category
            break # Assign the first matching category from the priority list

    # --- NEW: Extraction of WhatsApp, WhatsApp Group, and Region ---
    # These extractions use the cleaned bio text

    # Extract WhatsApp number (E.164 format and common variations)
    whatsapp_number_match = re.search(r'\+?\d{1,4}[-.\s]?\(?\d{1,}\)?[-.\s]?\d{1,}[-.\s]?\d{1,}[-.\s]?\d{1,}', cleaned_bio_text)
    profile_data["WhatsApp Number"] = whatsapp_number_match.group(0).strip() if whatsapp_number_match else ""

    # Extract WhatsApp Group Link
    whatsapp_group_link_match = re.search(r'chat\.whatsapp\.com/(?:invite/)?([a-zA-Z0-9]{22})', cleaned_bio_text)
    profile_data["WhatsApp Group Link"] = f"https://chat.whatsapp.com/{whatsapp_group_link_match.group(1)}" if whatsapp_group_link_match else ""

    # Extract Region (very basic example, might need a more comprehensive list)
    # Using a broader list of LATAM regions for better coverage
    regions = [
        "argentina", "chile", "colombia", "ecuador", "méxico", "perú", "venezuela",
        "brasil", "bolivia", "paraguay", "uruguay", "panamá", "costa rica", "guatemala",
        "honduras", "el salvador", "nicaragua", "cuba", "dominicana", "puerto rico"
    ]
    detected_regions = [r for r in regions if r in cleaned_bio_text.lower()] # Use cleaned bio for region detection
    profile_data["Region"] = ", ".join(detected_regions) if detected_regions else ""

    # Adjust classification based on extracted contact info, if not already a more specific category
    if profile_data["WhatsApp Number"] or profile_data["WhatsApp Group Link"]:
        if classification == "Other" or classification == "Phone & Accessories":
            classification = "Potentially Relevant" # Mark as 'Potentially Relevant' if contact info is found and no stronger classification applies

    # --- GPT Integration (Optional - Uncomment and configure if needed) ---
    # To use GPT, you'll need to set OPENAI_API_KEY in your .env file
    # and potentially configure a 'use_gpt_classification' flag in config.yaml
    #
    # if os.getenv("USE_GPT_CLASSIFICATION", "False").lower() == "true":
    #    try:
    #        # Example prompt - refine as needed for better results
    #        prompt = (
    #            f"Classify the following Instagram profile into one of these categories: "
    #            f"Retailer, Reseller, Distributor, Repair Shop, Phone & Accessories, Other. "
    #            f"Base your decision on the profile's Bio: \"{profile_data.get('Bio', '')}\", " # Note: This will use the cleaned bio
    #            f"Full Name: \"{profile_data.get('Full Name', '')}\", "
    #            f"and External Link: \"{profile_data.get('External Link', '')}\". "
    #            f"Return only the category name."
    #        )
    #        response = openai.chat.completions.create(
    #            model="gpt-3.5-turbo", # or "gpt-4o" for newer models
    #            messages=[{"role": "user", "content": prompt}],
    #            max_tokens=20, # Keep short for just the category name
    #            temperature=0.0 # For consistent output
    #        )
    #        gpt_classification = response.choices[0].message.content.strip()
    #        # Validate GPT's response against expected categories
    #        if gpt_classification in CLASSIFICATION_RULES.keys() or gpt_classification in ["Other", "Potentially Relevant", "Phone & Accessories"]:
    #            classification = gpt_classification
    #            # print(f"    AI Classified as: {classification}") # Optional: print from classifier
    #        else:
    #            # print(f"    AI Classification inconclusive: '{gpt_classification}'. Falling back to rule-based.")
    #            pass # Fallback to rule-based if GPT output is not recognized
    #    except Exception as e:
    #        # print(f"    Error with GPT classification: {e}. Falling back to rule-based.")
    #        pass
             
    # Ensure classification is stored in profile_data before returning
    profile_data["Classification"] = classification
    return classification