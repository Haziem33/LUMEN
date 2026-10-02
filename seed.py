"""بيبني الـ database ويملاها من data.py. شغّله: python seed.py
تحذير: بيمسح lumin.db ويبنيها من الأول (مناسب للتطوير فقط)."""
from app import app
from models import db, Category, Term, Translation, TermSpec, Source, Related
from search_utils import normalize
from data import TERMS

CATS = {  # English: (Arabic, Spanish)
    "Worship": ("العبادات", "Adoración"),
    "Jurisprudence": ("الفقه", "Jurisprudencia"),
    "Creed": ("العقيدة", "Credo"),
    "Ethics & Society": ("الأخلاق والمجتمع", "Ética y sociedad"),
}

with app.app_context():
    db.drop_all()
    db.create_all()
    cats = {en: Category(name_en=en, name_ar=ar, name_es=es) for en, (ar, es) in CATS.items()}
    db.session.add_all(cats.values())

    for d in TERMS:
        t = Term(translit=d["translit"], translit_norm=normalize(d["translit"]),
                 root_ar=d["root"], root_latin=d["root_latin"], category=cats[d["category"]])
        for lang, title, gloss, definition in [
            ("ar", d["ar"], "", d["def_ar"]),
            ("en", d["en"], d["gloss_en"], d["def_en"]),
            ("es", d["es"], d["gloss_es"], d["def_es"]),
        ]:
            t.translations.append(Translation(lang=lang, title=title, gloss=gloss,
                                              definition=definition, search_text=normalize(title)))
        t.specs = [TermSpec(label=a, label_ar=b, value=c) for a, b, c in d["specs"]]
        t.sources = [Source(citation=r) for r in d["refs"]]
        t.related = [Related(label=r) for r in d["related"]]
        db.session.add(t)

    db.session.commit()
    print("Done:", Term.query.count(), "terms seeded.")
