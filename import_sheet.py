"""تحديث يدوي كامل من الشيت (بيمسح الـ database ويبنيها من الأول):
    python import_sheet.py              ← من Google Sheets
    python import_sheet.py csv_folder   ← من ملفات CSV (Categories.csv و Terms.csv و Sources.csv)
الموقع نفسه بيحدّث نفسه تلقائيًا، فالسكريبت ده للطوارئ أو لإعادة البناء بعد تغيير الجداول."""
import os, sys
os.environ["DISABLE_SYNC"] = "1"
from app import app
from models import db
from sheet_sync import rebuild

with app.app_context():
    db.drop_all(); db.create_all()
msg, warn = rebuild(app, sys.argv[1] if len(sys.argv) > 1 else None)
print("تم:", msg)
for w in warn:
    print("تنبيه:", w)
