# classifier/classifier.py

class ProfileClassifier:
    def __init__(self, rules):
        self.rules = {k: set(kw.lower() for kw in v) for k, v in rules.items()}

    def classify(self, bio):
        if not bio:
            return "unknown"
        bio_lower = bio.lower()
        for label, keywords in self.rules.items():
            if any(keyword in bio_lower for keyword in keywords):
                return label
        return "unknown"

# Add this function for backward compatibility
def classify_profile(profile_data):
    rules = {
        "reseller": ["reseller", "distributor", "retailer"],
        "repair": ["repair", "fix", "service"]
    }
    classifier = ProfileClassifier(rules)
    return classifier.classify(profile_data.get("bio", ""))
