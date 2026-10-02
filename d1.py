from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import CellIsRule
from openpyxl.utils import get_column_letter

path = "E:/LUMEN/LUMEN_Content_Database_Template.xlsx"

wb = Workbook()
ws_readme = wb.active
ws_readme.title = "README"
ws_cat = wb.create_sheet("CATEGORIES")
ws_terms = wb.create_sheet("TERMS")
ws_sources = wb.create_sheet("SOURCES")

# LUMEN-inspired neutral palette (easy to replace with exact brand colors later)
navy = "18243A"
accent = "D8A84E"
light = "F5F7FA"
input_fill = "FFFDF5"
auto_fill = "EAF0F7"
white = "FFFFFF"
green = "D9EAD3"
yellow = "FFF2CC"
red = "F4CCCC"
border_color = "D9DEE7"

thin = Side(style="thin", color=border_color)

def style_header(ws, row, cols):
    for c in range(1, cols + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = PatternFill("solid", fgColor=navy)
        cell.font = Font(color=white, bold=True)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = Border(bottom=thin)

# README
readme_rows = [
    ["LUMEN — Content Database Template"],
    ["Purpose", "This workbook is the structured content-entry template for the LUMEN Islamic dictionary."],
    ["Workflow", "1) Add/confirm categories → 2) Add terms and translations → 3) Add sources → 4) Review confirmation status → 5) Import into LUMEN."],
    ["Important", "Do not manually edit Category Codes or Term IDs. Use dropdowns wherever available."],
    ["Term ID format", "CAT001T001 = Category CAT001 + Term 001 within that category."],
    ["Confirmation", "Pending = not reviewed | Confirmed = reviewed/approved | Needs Revision = changes required."],
    ["Sources", "Sources are linked to individual Terms, not directly to Categories."],
    ["Arabic", "Enter the Arabic term and its Arabic definition in the dedicated columns."],
    ["Spanish", "Enter the Spanish term and its Spanish definition in the dedicated columns."],
    ["English", "Enter the English term and its English definition in the dedicated columns."],
    ["Rule", "Do not invent a translation or source. If uncertain, use Needs Revision and leave a note externally."],
]
for r, row in enumerate(readme_rows, 1):
    for c, value in enumerate(row, 1):
        ws_readme.cell(r, c, value)
ws_readme.merge_cells("A1:B1")
ws_readme["A1"].fill = PatternFill("solid", fgColor=navy)
ws_readme["A1"].font = Font(color=white, bold=True, size=16)
ws_readme["A1"].alignment = Alignment(horizontal="center")
for r in range(2, len(readme_rows)+1):
    ws_readme.cell(r,1).font = Font(bold=True)
    ws_readme.cell(r,1).fill = PatternFill("solid", fgColor=accent)
    ws_readme.cell(r,2).alignment = Alignment(wrap_text=True, vertical="top")
    ws_readme.cell(r,1).border = Border(bottom=thin)
    ws_readme.cell(r,2).border = Border(bottom=thin)
ws_readme.column_dimensions["A"].width = 22
ws_readme.column_dimensions["B"].width = 105
ws_readme.freeze_panes = "A2"

# Categories
headers = ["Category Code", "Category Name", "Description"]
for i,h in enumerate(headers,1): ws_cat.cell(1,i,h)
style_header(ws_cat,1,3)
examples = [
    ["CAT001","Zakat","Terms related to Zakat"],
    ["CAT002","Prayer","Terms related to Prayer"],
    ["CAT003","Fasting","Terms related to Fasting"],
    ["CAT004","Hajj","Terms related to Hajj"],
    ["CAT005","Umrah","Terms related to Umrah"],
    ["CAT006","Quran","Quran-related terminology"],
    ["CAT007","Hadith","Hadith-related terminology"],
]
for r,row in enumerate(examples,2):
    for c,v in enumerate(row,1):
        ws_cat.cell(r,c,v)
        ws_cat.cell(r,c).fill = PatternFill("solid", fgColor=input_fill if c==2 else auto_fill)
        ws_cat.cell(r,c).border = Border(bottom=thin)
ws_cat.column_dimensions["A"].width = 18
ws_cat.column_dimensions["B"].width = 25
ws_cat.column_dimensions["C"].width = 60
ws_cat.freeze_panes = "A2"
ws_cat.auto_filter.ref = "A1:C1000"

# Terms
term_headers = [
    "Category","Term ID","Arabic Term","Arabic Definition",
    "Spanish Term","Spanish Definition","English Term","English Definition","Confirmation"
]
for i,h in enumerate(term_headers,1): ws_terms.cell(1,i,h)
style_header(ws_terms,1,9)

# Put formulas for rows 2:1001.
# Uses category name in A, looks up category code, and counts prior terms of same category.
# This is designed to be copied/imported into Google Sheets.
for r in range(2,1002):
    ws_terms.cell(r,2, f'=IF(A{r}="","",IFERROR(VLOOKUP(A{r},CATEGORIES!$B$2:$A$1000,2,FALSE),"")&"T"&TEXT(COUNTIF($A$2:A{r},A{r}),"000"))')
    ws_terms.cell(r,2).fill = PatternFill("solid", fgColor=auto_fill)
    for c in [1,3,4,5,6,7,8,9]:
        ws_terms.cell(r,c).fill = PatternFill("solid", fgColor=input_fill)
    for c in range(1,10):
        ws_terms.cell(r,c).border = Border(bottom=thin)
        ws_terms.cell(r,c).alignment = Alignment(vertical="top", wrap_text=True)

# NOTE: Excel VLOOKUP can't look left. Replace formula with INDEX/MATCH for compatibility.
for r in range(2,1002):
    ws_terms.cell(r,2, f'=IF(A{r}="","",IFERROR(INDEX(CATEGORIES!$A$2:$A$1000,MATCH(A{r},CATEGORIES!$B$2:$B$1000,0)),"")&"T"&TEXT(COUNTIF($A$2:A{r},A{r}),"000"))')

# Data validation: category dropdown
cat_dv = DataValidation(type="list", formula1="=CATEGORIES!$B$2:$B$1000", allow_blank=True)
cat_dv.error = "Please select a category from the dropdown."
cat_dv.errorTitle = "Invalid Category"
cat_dv.prompt = "Select a category from the CATEGORIES sheet."
cat_dv.promptTitle = "LUMEN Category"
ws_terms.add_data_validation(cat_dv)
cat_dv.add("A2:A1001")

# Confirmation dropdown
conf_dv = DataValidation(type="list", formula1='"Pending,Confirmed,Needs Revision"', allow_blank=True)
conf_dv.error = "Choose Pending, Confirmed, or Needs Revision."
conf_dv.errorTitle = "Invalid Status"
ws_terms.add_data_validation(conf_dv)
conf_dv.add("I2:I1001")

# Conditional formatting
ws_terms.conditional_formatting.add("I2:I1001", CellIsRule(operator="equal", formula=['"Confirmed"'], fill=PatternFill("solid", fgColor=green)))
ws_terms.conditional_formatting.add("I2:I1001", CellIsRule(operator="equal", formula=['"Pending"'], fill=PatternFill("solid", fgColor=yellow)))
ws_terms.conditional_formatting.add("I2:I1001", CellIsRule(operator="equal", formula=['"Needs Revision"'], fill=PatternFill("solid", fgColor=red)))

widths = [20,18,24,55,24,55,24,55,20]
for i,w in enumerate(widths,1): ws_terms.column_dimensions[get_column_letter(i)].width = w
ws_terms.freeze_panes = "A2"
ws_terms.auto_filter.ref = "A1:I1001"

# Sources
source_headers = ["Source ID","Term ID","Source Title","Author","Type","Reference","URL"]
for i,h in enumerate(source_headers,1): ws_sources.cell(1,i,h)
style_header(ws_sources,1,7)

for r in range(2,1002):
    # Source ID intentionally formula-based for template convenience.
    ws_sources.cell(r,1, f'=IF(C{r}="","","SRC"&TEXT(ROW()-1,"000"))')
    ws_sources.cell(r,1).fill = PatternFill("solid", fgColor=auto_fill)
    for c in range(2,8):
        ws_sources.cell(r,c).fill = PatternFill("solid", fgColor=input_fill)
    for c in range(1,8):
        ws_sources.cell(r,c).border = Border(bottom=thin)
        ws_sources.cell(r,c).alignment = Alignment(vertical="top", wrap_text=True)

# Term ID dropdown. Since Excel validation doesn't support a dynamic cross-sheet direct reference,
# use a named range via defined name.
from openpyxl.workbook.defined_name import DefinedName
wb.defined_names.add(DefinedName("TermIDs", attr_text="'TERMS'!$B$2:$B$1001"))
term_dv = DataValidation(type="list", formula1="=TermIDs", allow_blank=True)
term_dv.error = "Please select a Term ID from the TERMS sheet."
term_dv.errorTitle = "Invalid Term ID"
ws_sources.add_data_validation(term_dv)
term_dv.add("B2:B1001")

type_dv = DataValidation(type="list", formula1='"Quran,Hadith,Book,Article,Website,Scholar,Other"', allow_blank=True)
ws_sources.add_data_validation(type_dv)
type_dv.add("E2:E1001")

source_widths = [16,20,40,25,18,35,55]
for i,w in enumerate(source_widths,1): ws_sources.column_dimensions[get_column_letter(i)].width = w
ws_sources.freeze_panes = "A2"
ws_sources.auto_filter.ref = "A1:G1001"

# Sheet tabs
ws_readme.sheet_properties.tabColor = navy
ws_cat.sheet_properties.tabColor = accent
ws_terms.sheet_properties.tabColor = "5B9BD5"
ws_sources.sheet_properties.tabColor = "70AD47"

# Workbook active sheet
wb.active = 0

# Add a note in Terms about the ID formula
ws_terms["B1"].comment = None

# Save
wb.save(path)

print(f"Created: {path}")
