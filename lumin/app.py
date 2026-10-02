import os
from flask import Flask, render_template, request, abort
from sqlalchemy import or_
from models import db, Term, Translation, Category
from search_utils import normalize

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "lumin.db")
db.init_app(app)


@app.context_processor
def globals_():
    lang = request.args.get("lang", "en")
    return {"lang": lang, "dir": "rtl" if lang == "ar" else "ltr"}


def published():
    return Term.query.filter_by(status="published")


@app.route("/")
def home():
    terms = [t.to_view() for t in published().order_by(Term.id).all()]
    return render_template("index.html", terms=terms)


@app.route("/search")
def search():
    q = request.args.get("q", "").strip()
    cats = request.args.getlist("cat")
    query = published()
    qn = normalize(q)
    if qn:
        like = f"%{qn}%"
        query = (query.outerjoin(Translation)
                 .filter(or_(Translation.search_text.like(like), Term.translit_norm.like(like)))
                 .distinct())
    if cats:
        query = query.join(Category).filter(Category.name_en.in_(cats))
    results = [t.to_view() for t in query.order_by(Term.id).all()]
    categories = [c.name_en for c in Category.query.order_by(Category.id)]
    return render_template("search.html", q=q, cats=cats, results=results, categories=categories)


@app.route("/term/<int:term_id>")
def term(term_id):
    t = published().filter_by(id=term_id).first()
    if not t:
        abort(404)
    return render_template("term.html", t=t.to_view())


if __name__ == "__main__":
    app.run(debug=True)
