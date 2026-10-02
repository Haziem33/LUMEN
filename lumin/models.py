from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name_en = db.Column(db.String(80), unique=True, nullable=False)
    name_ar = db.Column(db.String(80))
    name_es = db.Column(db.String(80))


class Term(db.Model):
    """المصطلح نفسه (الحاجات المشتركة بين اللغات)."""
    id = db.Column(db.Integer, primary_key=True)
    translit = db.Column(db.String(120))
    translit_norm = db.Column(db.String(120), index=True)
    root_ar = db.Column(db.String(20))
    root_latin = db.Column(db.String(20))
    status = db.Column(db.String(20), default="published")  # draft / published
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))

    category = db.relationship("Category")
    translations = db.relationship("Translation", backref="term", cascade="all, delete-orphan")
    specs = db.relationship("TermSpec", cascade="all, delete-orphan")
    sources = db.relationship("Source", cascade="all, delete-orphan")
    related = db.relationship("Related", cascade="all, delete-orphan")

    def tr(self, lang):
        found = next((t for t in self.translations if t.lang == lang), None)
        return found or Translation(lang=lang, title="", gloss="", definition="")

    def to_view(self):
        """بيرجع نفس شكل القاموس اللي كانت بتستخدمه الـ templates، فمفيش HTML اتغيّر."""
        ar, en, es = self.tr("ar"), self.tr("en"), self.tr("es")
        return {
            "id": self.id, "translit": self.translit,
            "root": self.root_ar, "root_latin": self.root_latin,
            "category": self.category.name_en if self.category else "",
            "ar": ar.title, "en": en.title, "es": es.title,
            "gloss_en": en.gloss, "gloss_es": es.gloss,
            "def_ar": ar.definition, "def_en": en.definition, "def_es": es.definition,
            "specs": [(s.label, s.label_ar, s.value) for s in self.specs],
            "related": [r.label for r in self.related],
            "refs": [s.citation for s in self.sources],
            "sources": len(self.sources), "related_count": len(self.related),
        }


class Translation(db.Model):
    """صف لكل (مصطلح + لغة). إضافة لغة رابعة = صفوف جديدة بس، من غير تعديل الجداول."""
    __table_args__ = (db.UniqueConstraint("term_id", "lang"),)
    id = db.Column(db.Integer, primary_key=True)
    term_id = db.Column(db.Integer, db.ForeignKey("term.id"), nullable=False)
    lang = db.Column(db.String(2), nullable=False)  # ar / en / es
    title = db.Column(db.String(200))
    gloss = db.Column(db.String(200))
    definition = db.Column(db.Text)
    search_text = db.Column(db.Text, index=True)    # العنوان بعد التطبيع


class TermSpec(db.Model):
    """حقول اختيارية (زي نسبة الزكاة). المصطلح اللي مالوش مواصفات مبياخدش صفوف."""
    id = db.Column(db.Integer, primary_key=True)
    term_id = db.Column(db.Integer, db.ForeignKey("term.id"), nullable=False)
    label = db.Column(db.String(100))
    label_ar = db.Column(db.String(100))
    value = db.Column(db.String(200))


class Source(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    term_id = db.Column(db.Integer, db.ForeignKey("term.id"), nullable=False)
    citation = db.Column(db.String(300))


class Related(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    term_id = db.Column(db.Integer, db.ForeignKey("term.id"), nullable=False)
    label = db.Column(db.String(120))
