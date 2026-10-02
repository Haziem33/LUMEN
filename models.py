from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)   # CAT001
    name_ar = db.Column(db.String(120))
    name_es = db.Column(db.String(120))
    name_en = db.Column(db.String(120))
    reading = db.Column(db.String(120))

    def to_view(self):
        return {"code": self.code, "ar": self.name_ar or "", "es": self.name_es or "",
                "en": self.name_en or "", "reading": self.reading or ""}


class Term(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)  # CAT001T001
    status = db.Column(db.String(20), default="draft")                         # draft / review / confirmed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))

    category = db.relationship("Category")
    translations = db.relationship("Translation", backref="term", cascade="all, delete-orphan")
    sources = db.relationship("Source", cascade="all, delete-orphan")

    def tr(self, lang):
        found = next((t for t in self.translations if t.lang == lang), None)
        return found or Translation(lang=lang, title="", definition="")

    def to_view(self):
        ar, en, es = self.tr("ar"), self.tr("en"), self.tr("es")
        return {"code": self.code, "ar": ar.title, "en": en.title, "es": es.title,
                "def_ar": ar.definition, "def_en": en.definition, "def_es": es.definition,
                "cat": self.category.to_view() if self.category else {"code": "", "ar": "", "en": "", "es": "", "reading": ""},
                "refs": [{"short": s.short_ref or "", "full": s.citation or ""} for s in self.sources]}


class Translation(db.Model):
    __table_args__ = (db.UniqueConstraint("term_id", "lang"),)
    id = db.Column(db.Integer, primary_key=True)
    term_id = db.Column(db.Integer, db.ForeignKey("term.id"), nullable=False)
    lang = db.Column(db.String(2), nullable=False)
    title = db.Column(db.String(200))
    definition = db.Column(db.Text)
    search_text = db.Column(db.Text, index=True)


class Source(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    term_id = db.Column(db.Integer, db.ForeignKey("term.id"), nullable=False)
    short_ref = db.Column(db.String(200))
    citation = db.Column(db.String(500))
