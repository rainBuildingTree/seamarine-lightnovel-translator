import re
import string

def contains_japanese(text: str) -> bool:
    filtered = re.sub(r'[・ー]', '', text)
    return re.search(r'[\u3040-\u30FF\u4E00-\u9FFF]', filtered) is not None

def contains_cyrill(text: str) -> bool:
    return re.search(r'[\u0400-\u04FF\u0500-\u052F]', text) is not None

def contains_thai(text: str) -> bool:
    return re.search(r'[\u0E00-\u0E7F]', text) is not None

def contains_arabic(text: str) -> bool:
    return re.search(r'[\u0600-\u06FF\u0750-\u077F]', text) is not None

def contains_hebrew(text: str) -> bool:
    return re.search(r'[\u0590-\u05FF]', text) is not None

def contains_devanagari(text: str) -> bool:
    return re.search(r'[\u0900-\u097F]', text) is not None

def contains_english(text: str) -> bool:
    english_char_count = sum(1 for c in text if c in string.ascii_letters)
    total_alpha_count = sum(1 for c in text if c.isalpha())
    if total_alpha_count == 0:
        return False
    return english_char_count / total_alpha_count > 0.5

def contains_foreign(text: str, is_include_english: bool = False) -> bool:
    return (contains_arabic(text) or contains_japanese(text) or contains_cyrill(text) or
            (contains_english(text) if is_include_english else False) or
            contains_thai(text) or contains_hebrew(text) or contains_devanagari(text))