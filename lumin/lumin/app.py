from flask import Flask, render_template, request, abort
from data import TERMS, CATEGORIES

app = Flask(__name__)

@app.context_processor
def globals_():
    lang = request.args.get("lang", "en")
    return {"lang": lang, "dir": "rtl" if lang == "ar" else "ltr"}

@app.route("/")
def home():
    return render_template("index.html", terms=TERMS)

@app.route("/search")
def search():
    q = request.args.get("q", "").strip()
    cats = request.args.getlist("cat")
    ql = q.lower()
    results = [t for t in TERMS
               if (not ql or ql in t["en"].lower() or ql in t["es"].lower()
                   or ql in t["translit"].lower() or q in t["ar"])
               and (not cats or t["category"] in cats)]
    return render_template("search.html", q=q, cats=cats, results=results, categories=CATEGORIES)

@app.route("/term/<int:term_id>")
def term(term_id):
    t = next((x for x in TERMS if x["id"] == term_id), None)
    if not t:
        abort(404)
    return render_template("term.html", t=t)

if __name__ == "__main__":
    app.run(debug=True)
