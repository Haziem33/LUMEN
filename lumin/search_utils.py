"""تطبيع النص قبل البحث: بيخلي 'الزَّكَاة' و'الزكاة' و'Zakāh' و'zakah' يتطابقوا."""
import re, unicodedata

_AR_MARKS = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED\u0640]")  # تشكيل + تطويل

def normalize(text):
    if not text:
        return ""
    text = _AR_MARKS.sub("", text)
    text = re.sub("[إأآٱ]", "ا", text).replace("ى", "ي").replace("ة", "ه")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))  # ā -> a ، ṣ -> s
    text = re.sub(r"[^\w\s]|_", " ", text.lower())                   # شرطات وفواصل عليا
    return re.sub(r"\s+", " ", text).strip()
