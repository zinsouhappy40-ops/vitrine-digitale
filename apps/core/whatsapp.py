import re
from urllib.parse import urlencode


DEFAULT_MESSAGE = "Bonjour, je suis intéressé(e) par vos produits."


def build_whatsapp_url(number, product_name=None):
    if not number:
        return None
    raw_number = str(number).strip()
    if not re.fullmatch(r"[+\d\s().-]+", raw_number):
        return None
    normalized_number = re.sub(r"\D", "", raw_number)
    if not re.fullmatch(r"[1-9]\d{7,14}", normalized_number):
        return None

    message = (
        f"Bonjour, je suis intéressé(e) par : {product_name}."
        if product_name
        else DEFAULT_MESSAGE
    )
    return f"https://wa.me/{normalized_number}?{urlencode({'text': message})}"
