"""قراءة وفحص الشيت وتحديث قاعدة البيانات منه (بيستخدمه الموقع تلقائيًا وسكريبت import_sheet.py).
    python import_sheet.py              ← من Google Sheets مباشرة (الشيت لازم يكون: Anyone with the link = Viewer)
    python import_sheet.py csv_folder   ← من ملفات CSV محمّلة: Categories.csv و Terms.csv و Sources.csv
"""
import csv, io, os, re, sys, urllib.parse, urllib.request

SHEET_ID = os.environ.get("SHEET_ID", "1E-G95N0uyrnhY5zrmRjl2hj1VSrRRiyfWBf4-ExUghw")
FIELDS = ["Title AR", "Definition AR", "Title ES", "Definition ES", "Title EN", "Definition EN"]


def read_tab(tab, folder=None):
    if folder:
        with open(os.path.join(folder, tab + ".csv"), encoding="utf-8-sig", newline="") as f:
            text = f.read()
    else:
        url = "https://docs.google.com/spreadsheets/d/%s/gviz/tq?tqx=out:csv&sheet=%s" % (SHEET_ID, urllib.parse.quote(tab))
        with urllib.request.urlopen(url) as r:
            text = r.read().decode("utf-8")
    return [{k.strip(): (v or "").strip() for k, v in row.items() if k} for row in csv.DictReader(io.StringIO(text))]


def clean(cats, terms, sources):
    """بيفحص الصفوف ويرجّع (فصول، مصطلحات، مراجع، تحذيرات)."""
    warn, out_cats, out_terms, out_src, seen = [], {}, {}, [], {}
    for c in cats:
        if c.get("Code") and (c.get("Name EN") or c.get("Name AR")):
            out_cats[c["Code"]] = c
    for r in terms:
        code = r.get("Code (auto)", "")
        if not code:
            continue
        if code in out_terms:
            warn.append(f"{code}: الكود مكرر، اتجاهل الصف التاني"); continue
        m = re.match(r"(CAT\d{3})", r.get("Category", ""))
        cat = m.group(1) if m else ""
        if cat not in out_cats:
            warn.append(f"{code}: الفصل '{r.get('Category', '')}' مش موجود في شيت Categories، اتجاهل"); continue
        if not code.startswith(cat):
            warn.append(f"{code}: الكود مش بيطابق الفصل {cat}")
        status = r.get("Confirmation", "").lower() or "draft"
        if status not in ("draft", "review", "confirmed"):
            warn.append(f"{code}: حالة غير معروفة '{status}'، اتحسبت draft"); status = "draft"
        missing = [f for f in FIELDS if not r.get(f)]
        if status == "confirmed" and missing:
            warn.append(f"{code}: confirmed بس ناقص ({', '.join(missing)})، اتحوّل لـ review"); status = "review"
        for f in ("Definition AR", "Definition ES", "Definition EN"):
            d = r.get(f)
            if d:
                if d in seen and seen[d] != code:
                    warn.append(f"{code}: {f} مطابق تمامًا لتعريف {seen[d]}، راجعوه")
                seen.setdefault(d, code)
        out_terms[code] = dict(r, status=status, cat=cat)
    for s in sources:
        code = s.get("Term code", "")
        if not code:
            continue
        if code not in out_terms:
            warn.append(f"Sources: الكود {code} مش موجود في Terms، اتجاهل")
        else:
            out_src.append(s)
    return out_cats, out_terms, out_src, warn


def rebuild(app, folder=None):
    """بيحدّث الـ database من الشيت داخل transaction واحدة (لو فشل السحب، البيانات القديمة تفضل زي ما هي)."""
    from models import db, Category, Term, Translation, Source
    from search_utils import normalize
    cats, terms, srcs, warn = clean(read_tab("Categories", folder), read_tab("Terms", folder), read_tab("Sources", folder))
    if not cats or not terms:
        raise RuntimeError("الشيت رجع بدون فصول أو مصطلحات (اتأكدي إنه Anyone with the link = Viewer). التحديث اتجاهل.")
    with app.app_context():
        try:
            for m in (Source, Translation, Term, Category):
                db.session.query(m).delete()
            cmap, tmap = {}, {}
            for code, c in cats.items():
                cmap[code] = Category(code=code, name_ar=c.get("Name AR"), name_es=c.get("Name ES"),
                                      name_en=c.get("Name EN") or c.get("Name AR"), reading=c.get("Reading (transliteration)"))
                db.session.add(cmap[code])
            for code, r in terms.items():
                t = Term(code=code, status=r["status"], category=cmap[r["cat"]])
                for lang, k in (("ar", "AR"), ("es", "ES"), ("en", "EN")):
                    title = r.get("Title " + k, "")
                    t.translations.append(Translation(lang=lang, title=title, definition=r.get("Definition " + k, ""),
                                                      search_text=normalize(title)))
                db.session.add(t); tmap[code] = t
            for s in srcs:
                tmap[s["Term code"]].sources.append(Source(short_ref=s.get("Short reference"), citation=s.get("Full citation")))
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
    live = sum(1 for r in terms.values() if r["status"] == "confirmed")
    return f"{len(cats)} فصل، {len(terms)} مصطلح ({live} confirmed ظاهرين في الموقع)، {len(srcs)} مرجع", warn
