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
# The 'Phone & Accessories' category will now dynamically include keywords from config.yaml.
CLASSIFICATION_RULES = {
    "Retailer": ["venta", "tienda", "local", "compra y venta", "cliente final", "store", "shop"],
    "Reseller": ["reventa", "oportunidad", "flipping", "mayoreo", "wholesale", "revendedor"],
    "Distributor": ["distribuidor", "mayorista", "suministros", "importador", "distribucion", "provider"],
    "Repair Shop": ["reparacion", "servicio tecnico", "arreglos", "diagnostico", "unlock", "repair"],
    "Phone & Accessories": CONFIG_KEYWORDS # Dynamically load keywords from config
}

def classify_profile(profile_data):
    """
    Classifies an Instagram profile based on its bio, full name, and external link.
    Uses rule-based keyword matching. Can be extended with GPT integration.
    """
    bio = profile_data.get("Bio", "").lower()
    full_name = profile_data.get("Full Name", "").lower()
    external_link = profile_data.get("External Link", "").lower()

    # Combine relevant text for classification
    text_to_classify = f"{bio} {full_name} {external_link}"
    
    classification = "Other" # Default classification

    # Rule-based classification
    # Iterate through categories and their keywords
    # Consider the order if some classifications should take precedence over others
    # For instance, a "Repair Shop" might also contain "Phone & Accessories" keywords,
    # if you want "Repair Shop" to be more specific, place it higher.
    
    # Prioritize more specific classifications if keywords overlap
    priority_categories = ["Repair Shop", "Distributor", "Reseller", "Retailer", "Phone & Accessories"]

    for category in priority_categories:
        keywords = CLASSIFICATION_RULES.get(category, [])
        if any(keyword in text_to_classify for keyword in keywords):
            classification = category
            break # Assign the first matching category from the priority list

    # --- GPT Integration (Optional - Uncomment and configure if needed) ---
    # To use GPT, you'll need to set OPENAI_API_KEY in your .env file
    # and potentially configure a 'use_gpt_classification' flag in config.yaml
    #
    # if os.getenv("USE_GPT_CLASSIFICATION", "False").lower() == "true":
    #     try:
    #         # Example prompt - refine as needed for better results
    #         prompt = (
    #             f"Classify the following Instagram profile into one of these categories: "
    #             f"Retailer, Reseller, Distributor, Repair Shop, Phone & Accessories, Other. "
    #             f"Base your decision on the profile's Bio: \"{profile_data.get('Bio', '')}\", "
    #             f"Full Name: \"{profile_data.get('Full Name', '')}\", "
    #             f"and External Link: \"{profile_data.get('External Link', '')}\". "
    #             f"Return only the category name."
    #         )
    #         response = openai.chat.completions.create(
    #             model="gpt-3.5-turbo", # or "gpt-4o" for newer models
    #             messages=[{"role": "user", "content": prompt}],
    #             max_tokens=20, # Keep short for just the category name
    #             temperature=0.0 # For consistent output
    #         )
    #         gpt_classification = response.choices[0].message.content.strip()
    #         # Validate GPT's response against expected categories
    #         if gpt_classification in CLASSIFICATION_RULES.keys() or gpt_classification in ["Other", "Phone & Accessories"]:
    #             classification = gpt_classification
    #             # print(f"    AI Classified as: {classification}") # Optional: print from classifier
    #         else:
    #             # print(f"    AI Classification inconclusive: '{gpt_classification}'. Falling back to rule-based.")
    #             pass # Fallback to rule-based if GPT output is not recognized
    #     except Exception as e:
    #         # print(f"    Error with GPT classification: {e}. Falling back to rule-based.")
    #         pass
            
    return classification