"""Read-only data verification, independent of the package generator.

Run with Python 3.10 or later. Only independent-checks.json is written.
No third-party libraries, generator imports or network access are required.
"""
import csv
import hashlib
import io
import json
import re
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parent
D = Decimal
issues = []
checks = []

def check(condition, label, detail=None):
    checks.append({"check": label, "passed": bool(condition)})
    if not condition:
        issues.append({"check": label, "detail": detail})

def read(name):
    raw = (ROOT / name).read_bytes()
    check(not raw.startswith(b"\xef\xbb\xbf"), f"{name}: no BOM")
    check(b"\r" not in raw, f"{name}: LF line endings")
    text = raw.decode("utf-8")
    parsed = list(csv.reader(io.StringIO(text, newline=chr(10))))
    check(len({len(row) for row in parsed}) == 1, f"{name}: consistent field count")
    check(len(parsed[0]) == len(set(parsed[0])), f"{name}: unique column names")
    return list(csv.DictReader(io.StringIO(text, newline=chr(10))))

sales = read("sales.csv")
messy = read("messy-sales.csv")
products = read("products.csv")
answers = read("answers.csv")
dictionary = read("dictionary.csv")
defects = read("defects.csv")
schema = json.loads((ROOT / "datapackage.json").read_text(encoding="utf-8"))
licenses = schema.get("licenses", [])
check(len(licenses) == 1 and licenses[0].get("name") == "CC0-1.0", "metadata declares CC0-1.0")
check(any(license_entry.get("path") == "https://creativecommons.org/publicdomain/zero/1.0/" for license_entry in licenses), "metadata links official CC0 dedication")
license_path = ROOT / "LICENSE.md"
check(license_path.is_file(), "LICENSE.md exists")
license_text = license_path.read_text(encoding="utf-8") if license_path.is_file() else ""
check("CC0 1.0 Universal" in license_text and "https://creativecommons.org/publicdomain/zero/1.0/legalcode" in license_text, "LICENSE.md names CC0 and links official legal code")
check("original data, teaching documents and scripts" in license_text, "CC0 declaration covers package data, teaching documents and scripts")
fields = list(sales[0])
by_id = {r["order_id"]: r for r in sales}
catalog = {r["product_id"]: r for r in products}

def net(r):
    if r["status"] != "Completed":
        return D("0.00")
    return (D(r["units"]) * D(r["unit_price_usd"]) * (1-D(r["discount_rate"]))).quantize(D("0.01"), rounding=ROUND_HALF_UP)

def total(rows):
    return sum((net(r) for r in rows), D("0.00"))

def parse_date(s):
    if re.fullmatch(r"\d{4}[-/]\d{2}[-/]\d{2}", s):
        y, m, day = map(int, re.split("[-/]", s))
    elif re.fullmatch(r"\d{2}/\d{2}/\d{4}", s):
        day, m, y = map(int, s.split("/"))
    else:
        raise ValueError(f"Unexpected date format: {s!r}")
    return date(y, m, day).isoformat()

check(len(sales) == 144, "clean count 144")
check(len(by_id) == len(sales), "clean primary keys unique")
check(len(products) == len(catalog) == 6, "catalog count and unique keys")
check(all(r["product_id"] in catalog for r in sales), "all sales foreign keys mapped")
check(all(D(r["unit_price_usd"]) == D(catalog[r["product_id"]]["list_price_usd"]) for r in sales), "sales prices equal catalog")
check(all(date.fromisoformat(r["order_date"]).isoformat() == r["order_date"] for r in sales), "canonical ISO clean dates")
check(all(1 <= int(r["units"]) <= 8 for r in sales), "units constraints")
check(all(D(r["discount_rate"]) in {D("0"),D(".05"),D(".10"),D(".15")} for r in sales), "documented discounts")
check(all(r["status"] in {"Completed","Returned","Cancelled"} for r in sales), "status constraints")
check(all(r["region"] in {"North","South","East","West"} for r in sales), "region constraints")
check(all(r["channel"] in {"Online","Retail","Wholesale"} for r in sales), "channel constraints")
check(all(re.fullmatch(r"ORD-\d{4}",r["order_id"]) for r in sales), "order ID pattern")
check(len(messy) == 148, "messy count 148")

raw_ids = Counter(r["order_id"] for r in messy)
duplicates = {k:v for k,v in raw_ids.items() if v>1}
check(sum(n-1 for n in raw_ids.values()) == 4, "four extra duplicate occurrences")
check(sum(n for n in duplicates.values()) == 8, "eight rows in duplicate pairs")
first = {}
actual_changes = {}
changed_regions = 0
invalid_dates = []
missing = []
reconciled = []
repairs = []
for r in messy:
    oid = r["order_id"]
    changed_regions += int(r["region"] != r["region"].replace("\u00a0", " ").strip())
    for f in fields:
        if r[f] == "": missing.append((oid, f))
    try:
        parsed_date = parse_date(r["order_date"])
    except ValueError:
        invalid_dates.append(oid)
        parsed_date = None
    if oid in first:
        check(r == first[oid], f"duplicate {oid} exact copy")
        continue
    first[oid] = r
    for f in fields:
        if r[f] != by_id[oid][f]:
            actual_changes[(oid,f)] = (r[f],by_id[oid][f])
    cleaned = dict(r)
    cleaned["region"] = r["region"].replace("\u00a0", " ").strip()
    cleaned["channel"] = r["channel"].strip().title()
    cleaned["product_id"] = r["product_id"].strip()
    cleaned["units"] = str(int(r["units"].strip())) if r["units"].strip() else None
    cleaned["unit_price_usd"] = D(r["unit_price_usd"].strip().replace("$", ""))
    cleaned["discount_rate"] = D(r["discount_rate"].strip().rstrip("%")) / (100 if r["discount_rate"].strip().endswith("%") else 1)
    cleaned["order_date"] = parsed_date
    for f in ["region", "units", "order_date"]:
        if cleaned[f] in (None, ""):
            repairs.append((oid,f,by_id[oid][f]))
            cleaned[f] = by_id[oid][f]
    for f in fields:
        lhs, rhs = cleaned[f], by_id[oid][f]
        if f in {"units","unit_price_usd","discount_rate"}:
            same = D(lhs) == D(rhs)
        else:
            same = lhs == rhs
        check(same, f"reconcile {oid}.{f}", {"cleaned":str(lhs),"truth":rhs})
    reconciled.append(cleaned)

manifest_changes = {(r["order_id"],r["field"]):(r["raw_value"],r["expected_value"]) for r in defects if r["field"] != "__row__"}
check(actual_changes == manifest_changes, "manifest equals all changed cells", {"actual": len(actual_changes),"manifest":len(manifest_changes)})
check(len(actual_changes) == 29, "29 altered cells")
manifest_dup_ids = sorted(r["order_id"] for r in defects if r["field"] == "__row__")
check(sorted(duplicates) == manifest_dup_ids, "manifest lists exactly duplicate IDs")
check(len(repairs) == 3, "only three ground-truth repairs")
check(set(first) == set(by_id), "all and only clean order IDs occur")

expected = {
    ("01","row_count"):str(len(sales)),
    ("01","first_date"):min(r["order_date"] for r in sales),
    ("01","last_date"):max(r["order_date"] for r in sales),
    ("02","completed_net_sales"):str(total(sales)),
    ("02","completed_orders"):str(sum(r["status"]=="Completed" for r in sales)),
    ("03","returned_orders"):str(sum(r["status"]=="Returned" for r in sales)),
    ("04","north_online_net_sales"):str(total(r for r in sales if r["region"]=="North" and r["channel"]=="Online")),
    ("05","february_net_sales"):str(total(r for r in sales if "2026-02-01" <= r["order_date"] < "2026-03-01")),
    ("06","P004_product_name"):catalog["P004"]["product_name"],
    ("06","office_net_sales"):str(total(r for r in sales if catalog[r["product_id"]]["category"]=="Office")),
    ("06","unmatched_products"):str(sum(r["product_id"] not in catalog for r in sales)),
    ("07","region_cells_changed"):str(changed_regions),
    ("07","region_cells_missing"):str(sum(r["region"].replace("\u00a0"," ").strip()=="" for r in messy)),
    ("08","extra_duplicate_rows"):str(sum(n-1 for n in raw_ids.values())),
    ("08","distinct_order_ids"):str(len(raw_ids)),
    ("09","invalid_calendar_dates"):str(len(invalid_dates)),
    ("09","valid_date_rows_before_dedup"):str(len(messy)-len(invalid_dates)),
    ("10","missing_required_fields"):str(len(missing)),
    ("10","irrecoverable_fields"):str(len(missing)+len(invalid_dates)),
    ("10","reconciled_rows"):str(len(reconciled)),
    ("10","reconciled_net_sales"):str(total(reconciled)),
}
saved_answers = {(r["exercise_id"],r["metric"]):r["value"] for r in answers}
check(len(saved_answers)==len(answers)==21, "21 unique answer rows")
check(expected == saved_answers, "all answer values independently recomputed", {"mismatches":[{"key":k,"expected":v,"saved":saved_answers.get(k)} for k,v in expected.items() if saved_answers.get(k)!=v]})

# Validate descriptor/header agreement, types and declared constraints directly.
resource_rows = {"sales":sales,"messy-sales":messy,"products":products,"dictionary":dictionary,"answers":answers,"defects":defects}
for resource in schema["resources"]:
    rows = resource_rows[resource["name"]]
    sch = resource["schema"]
    check([f["name"] for f in sch["fields"]] == list(rows[0]), f"{resource['name']}: schema/header match")
    for row in rows:
        for f in sch["fields"]:
            val = row[f["name"]]
            cons = f.get("constraints",{})
            check(not cons.get("required") or val != "", f"{resource['name']}.{f['name']}: required")
            if val == "": continue
            if f["type"] == "date": date.fromisoformat(val)
            if f["type"] == "integer": check(re.fullmatch(r"[+-]?\d+",val), f"{resource['name']}.{f['name']}: integer")
            if f["type"] in {"number","integer"}:
                number=D(val)
                check("minimum" not in cons or number >= D(str(cons["minimum"])), f"{resource['name']}.{f['name']}: minimum")
                check("maximum" not in cons or number <= D(str(cons["maximum"])), f"{resource['name']}.{f['name']}: maximum")
            check("enum" not in cons or val in cons["enum"], f"{resource['name']}.{f['name']}: enum")
            check("pattern" not in cons or re.fullmatch(cons["pattern"],val), f"{resource['name']}.{f['name']}: pattern")
    if "primaryKey" in sch:
        primary = sch["primaryKey"]
        check(len({r[primary] for r in rows})==len(rows), f"{resource['name']}: primary key")
    for fk in sch.get("foreignKeys",[]):
        target = resource_rows[fk["reference"]["resource"]]
        target_keys = {r[fk["reference"]["fields"]] for r in target}
        check(all(r[fk["fields"]] in target_keys for r in rows), f"{resource['name']}: foreign key")

for row in dictionary:
    resource_name = row["resource"]
    check(resource_name in resource_rows and row["field"] in resource_rows[resource_name][0], f"dictionary field {resource_name}.{row['field']} exists")
check(len(dictionary)==22, "dictionary covers all 22 source fields")
check({(r["resource"],r["field"]) for r in dictionary} == {(n,f) for n in ("sales","messy-sales","products") for f in resource_rows[n][0]}, "dictionary full source coverage")
for line in (ROOT/"checksums.sha256").read_text().splitlines():
    digest, name = line.split("  ",1)
    check(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest, f"checksum {name}")

monthly=defaultdict(lambda:D("0.00"))
category=defaultdict(lambda:D("0.00"))
for row in sales:
    monthly[row["order_date"][:7]] += net(row)
    category[catalog[row["product_id"]]["category"]] += net(row)
halfcent = [r["order_id"] for r in sales if r["status"]=="Completed" and (D(r["units"])*D(r["unit_price_usd"])*(1-D(r["discount_rate"]))*100)%1==D(".5")]
report = {"issues":issues,"check_count":len(checks),"passed":not issues,"expected_answers":[{"exercise_id":k[0],"metric":k[1],"value":v} for k,v in expected.items()],"status_counts":dict(Counter(r["status"] for r in sales)),"monthly_net_sales":dict(monthly),"category_net_sales":dict(category),"duplicate_ids":duplicates,"altered_cell_count":len(actual_changes),"altered_cell_groups":dict(Counter(r["defect_type"] for r in defects if r["field"]!="__row__")),"ground_truth_repairs":repairs,"invalid_date_ids":invalid_dates,"missing_required_cells":missing,"half_cent_completed_order_ids":halfcent,"scope":"CSV content, independent Decimal arithmetic, documented cleaning and record-level reconciliation, descriptor/header/types/constraints, dictionary coverage, CC0 declaration consistency and package hashes. No generator import.","native_spreadsheet_engine_tested":False,"limitations":["This verifier does not execute spreadsheet formulas in Excel or Google Sheets.","The documented spreadsheet formula uses integer unit-price cents and whole-percent discounts before line rounding; the independent reference uses exact Decimal half-up cents."]}
(ROOT/"independent-checks.json").write_text(json.dumps(report,indent=2,default=str)+"\n",encoding="utf-8")
print(json.dumps(report,indent=2,default=str))
raise SystemExit(0 if not issues else 1)
