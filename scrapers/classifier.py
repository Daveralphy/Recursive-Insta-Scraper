import os
import re
import yaml

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
    Performs bio cleaning, extracts contact information (including links), and applies rule-based classification.
    """
    raw_bio = profile_data.get("Bio", "") # Get the original raw bio
    full_name = profile_data.get("Full Name", "").lower()
    username = profile_data.get("Username", "").lower()
    
    # Get the existing External Link (from Instagram's dedicated field)
    # This will be used as a starting point for collecting all links.
    existing_external_link_from_ig = profile_data.get("External Link", "").strip()

    # --- Step 1: Initial Bio Cleaning (Full Name & Username Lines) ---
    bio_lines = raw_bio.strip().split('\n')
    cleaned_bio_lines = list(bio_lines) # Create a mutable copy to work with

    # Rule 1: If the first line of the bio matches the Full Name, remove it.
    if cleaned_bio_lines and full_name and cleaned_bio_lines[0].strip().lower() == full_name:
        cleaned_bio_lines.pop(0)

    # Rule 2: If the (now) first line of the bio matches the Username (ignoring '@'), remove it.
    if cleaned_bio_lines and username and cleaned_bio_lines[0].strip().lower().replace("@", "") == username:
        cleaned_bio_lines.pop(0)

    # Reconstruct the bio after initial cleaning
    temp_bio_text = '\n'.join(cleaned_bio_lines).strip()


    # --- Step 2: Extract and Remove Links from Bio ---
    # Regex to find common URL patterns (http/https, www, or bare domain)
    # This pattern tries to be comprehensive but might catch some non-URL words if they match domain patterns.
    url_pattern = r'(?:https?://|www\.)[^\s<>"]+|[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})?(?:/[^\s<>"]*)?'
    
    all_found_links = set() # Use a set to store unique links

    # Add any existing external link from Instagram's native field
    if existing_external_link_from_ig:
        all_found_links.add(existing_external_link_from_ig)

    # Find all links in the current bio text (after initial cleaning)
    matches_in_bio = re.findall(url_pattern, temp_bio_text, re.IGNORECASE)
    for link in matches_in_bio:
        # Simple standardization: ensure http:// or https:// prefix if missing for www. or bare domains
        if not link.startswith(('http://', 'https://')):
            if 'www.' in link.lower():
                link = 'http://' + link # Default to http for www.
            else:
                # If it's a bare domain without www. (e.g., example.com), we might assume http
                # This could be aggressive, but per "anything link", we include it.
                link = 'http://' + link # Default to http for bare domains
        all_found_links.add(link.strip())

    # Update the 'External Link' field in profile_data
    # Sort for consistent output, then join by comma and space
    profile_data["External Link"] = ", ".join(sorted(list(all_found_links))) if all_found_links else ""
    
    # Remove the found links from the bio text
    final_cleaned_bio_text = temp_bio_text
    for link_to_remove in all_found_links:
        # Use re.escape to handle special characters in the link when replacing
        escaped_link = re.escape(link_to_remove)
        # Replace the link with a space to avoid concatenating words, then clean up extra spaces
        final_cleaned_bio_text = re.sub(escaped_link, ' ', final_cleaned_bio_text, flags=re.IGNORECASE)
    
    final_cleaned_bio_text = re.sub(r'\s+', ' ', final_cleaned_bio_text).strip() # Consolidate multiple spaces
    profile_data["Bio"] = final_cleaned_bio_text # Update the 'Bio' field with links removed

    # --- Step 3: Classification and Other Extractions (using the final cleaned bio) ---
    # Combine relevant text for classification (use the bio AFTER all cleaning)
    text_to_classify = f"{profile_data['Bio'].lower()} {full_name} {profile_data['External Link'].lower()}"
    
    classification = "Other" # Default classification

    # Rule-based classification
    priority_categories = ["Repair Shop", "Distributor", "Reseller", "Retailer", "Phone & Accessories"]

    for category in priority_categories:
        keywords = CLASSIFICATION_RULES.get(category, [])
        if any(keyword in text_to_classify for keyword in keywords):
            classification = category
            break # Assign the first matching category from the priority list

    # Extract WhatsApp number (E.164 format and common variations)
    whatsapp_number_match = re.search(r'\+?\d{1,4}[-.\s]?\(?\d{1,}\)?[-.\s]?\d{1,}[-.\s]?\d{1,}[-.\s]?\d{1,}', profile_data["Bio"])
    profile_data["WhatsApp Number"] = whatsapp_number_match.group(0).strip() if whatsapp_number_match else ""

    # Extract WhatsApp Group Link
    whatsapp_group_link_match = re.search(r'chat\.whatsapp\.com/(?:invite/)?([a-zA-Z0-9]{22})', profile_data["Bio"])
    profile_data["WhatsApp Group Link"] = f"https://chat.whatsapp.com/{whatsapp_group_link_match.group(1)}" if whatsapp_group_link_match else ""

    # Extract Region
    regions = [
        "argentina", "chile", "colombia", "ecuador", "méxico", "perú", "venezuela",
        "brasil", "bolivia", "paraguay", "uruguay", "panamá", "costa rica", "guatemala",
        "honduras", "el salvador", "nicaragua", "cuba", "dominicana", "puerto rico",
        "argentinian", "chilean", "colombian", "ecuadorian", "mexican", "peruvian",
        "venezuelan", "brazilian", "bolivian", "paraguayan", "uruguayan", "panamanian",
        "costarican", "guatemalan", "honduran", "elsalvadoran", "nicaraguan", "cuban",
        "dominican", "puertorrican"
    ]
    detected_regions = [r for r in regions if r in profile_data["Bio"].lower()]
    profile_data["Region"] = ", ".join(detected_regions) if detected_regions else ""

    # Adjust classification based on extracted contact info, if not already a more specific category
    if profile_data["WhatsApp Number"] or profile_data["WhatsApp Group Link"]:
        if classification == "Other" or classification == "Phone & Accessories":
            classification = "Potentially Relevant"

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
    #        else:
    #            pass
    #    except Exception as e:
    #        pass
             
    # Ensure classification is stored in profile_data before returning
    profile_data["Classification"] = classification
    return classification