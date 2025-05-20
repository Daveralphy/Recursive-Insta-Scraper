# filters/keyword_filter.py

class KeywordFilter:
    def __init__(self, keywords):
        self.keywords = set(keyword.lower() for keyword in keywords)

    def matches(self, text):
        if not text:
            return False
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.keywords)


_phone_keywords = ['phone', 'call', 'contact', 'whatsapp']
_phone_filter = KeywordFilter(_phone_keywords)

def is_phone_related(text):
    return _phone_filter.matches(text)
