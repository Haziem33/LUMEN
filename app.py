import os, threading, time
from flask import Flask, render_template, request, abort
from sqlalchemy import or_
from models import db, Term, Translation, Category
from search_utils import normalize
from sheet_sync import rebuild

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "lumin.db")
db.init_app(app)


@app.context_processor
def globals_():
    lang = request.args.get("lang", "en")
    if lang not in ("ar", "en", "es"):
        lang = "en"
    return {"lang": lang, "dir": "rtl" if lang == "ar" else "ltr"}


def live():
    return Term.query.filter_by(status="confirmed")   # الموقع بيعرض المصطلحات confirmed بس


def cat_views():
    """الفصول اللي فيها مصطلحات confirmed بس (الفصل الفاضي مبيظهرش للزوار)."""
    out = []
    for c in Category.query.order_by(Category.code):
        v = c.to_view(); v["count"] = live().filter_by(category_id=c.id).count()
        if v["count"]:
            out.append(v)
    return out


@app.route("/")
def home():
    return render_template("index.html", categories=cat_views())


@app.route("/search")
def search():
    q = request.args.get("q", "").strip()
    cats = request.args.getlist("cat")
    query, qn = live(), normalize(q)
    if qn:
        query = (query.outerjoin(Translation)
                 .filter(Translation.search_text.like(f"%{qn}%")).distinct())
    if cats:
        query = query.join(Category).filter(Category.code.in_(cats))
    results = [t.to_view() for t in query.order_by(Term.code).all()]
    return render_template("search.html", q=q, cats=cats, results=results, categories=cat_views())


@app.route("/categories")
def categories():
    return render_template("categories.html", categories=cat_views())


@app.route("/category/<code>")
def category(code):
    c = Category.query.filter_by(code=code).first_or_404()
    terms = [t.to_view() for t in live().filter_by(category_id=c.id).order_by(Term.code)]
    return render_template("category.html", c=c.to_view(), terms=terms, show_refs=True)


@app.route("/term/<code>")
def term(code):
    t = live().filter_by(code=code).first()
    if not t:
        abort(404)
    return render_template("term.html", t=t.to_view())


# ---- تحديث تلقائي من الشيت: مرة عند التشغيل، وبعدها كل SYNC_MINUTES دقيقة ----
SYNC_MINUTES = int(os.environ.get("SYNC_MINUTES", "10"))


def sync_once():
    try:
        with app.app_context():
            db.create_all()
        msg, warn = rebuild(app)
        print("[sync] تم:", msg, flush=True)
        for w in warn:
            print("[sync] تنبيه:", w, flush=True)
    except Exception as e:
        print("[sync] فشل (البيانات القديمة لسه شغالة):", e, flush=True)


def _loop():
    while True:
        time.sleep(SYNC_MINUTES * 60)
        sync_once()


if os.environ.get("DISABLE_SYNC") != "1":
    sync_once()
    threading.Thread(target=_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
