import re
from langdetect import detect
from sentence_transformers import SentenceTransformer

# Load AI model for semantic matching
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

# Define relevant keywords for cellphone retailers in LATAM (Spanish & Portuguese)
KEYWORDS = [
    "celulares", "móvil", "tecnología", "mayorista", "tienda de móviles",
    "accesorios para celular", "distribuidor de smartphones", "telefone",
    "loja de celulares", "revendedor de celulares", "assistência técnica celular"
]

def extract_whatsapp_number(bio_text):
    """Extracts WhatsApp number from bio using regex."""
    phone_pattern = r"\+?\d{1,3}[\s\-]?\d{4,5}[\s\-]?\d{4}"
    phone_match = re.findall(phone_pattern, bio_text)
    
    return phone_match[0] if phone_match else ""

def is_relevant_bio(bio_text):
    """Uses AI to determine if a bio is cellphone-related in Spanish or Portuguese."""
    try:
        detected_lang = detect(bio_text)
        if detected_lang not in ["es", "pt"]:  # Only Spanish or Portuguese
            return False

        # AI-powered similarity check
        bio_embedding = model.encode(bio_text)
        keyword_embeddings = model.encode(KEYWORDS)

        # Compute similarity between bio and keywords
        for keyword_embedding in keyword_embeddings:
            similarity_score = model.similarity(bio_embedding, keyword_embedding)
            if similarity_score > 0.75:  # Threshold for relevance
                return True
    except Exception as e:
        print(f"⚠️ Language detection failed: {e}")
    return False
