# detectors/whatsapp_detector.py

import re

class WhatsAppDetector:
    @staticmethod
    def detect_numbers(text):
        if not text:
            return []
        patterns = [
            r"\+?\d{1,3}[\s-]?\d{6,14}",       # Phone numbers
            r"wa\.me\/(\d{6,14})",             # wa.me links
            r"Wsp[\s:]?(\d{6,14})",            # Wsp label + number
        ]
        numbers = set()
        for pattern in patterns:
            matches = re.findall(pattern, text, flags=re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    number = match[0]
                else:
                    number = match
                numbers.add(number.strip())
        return list(numbers)

    @staticmethod
    def detect_group_links(text):
        if not text:
            return []
        pattern = r"(https?:\/\/)?chat\.whatsapp\.com\/[a-zA-Z0-9]+"
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        return [m if m.startswith("http") else f"https://{m}" for m in matches]

def extract_whatsapp_info(text):
    numbers = WhatsAppDetector.detect_numbers(text)
    groups = WhatsAppDetector.detect_group_links(text)
    whatsapp_number = numbers[0] if numbers else ""
    whatsapp_group = groups[0] if groups else ""
    return whatsapp_number, whatsapp_group
