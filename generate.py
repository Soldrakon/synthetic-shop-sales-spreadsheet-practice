"""Rebuild this original teaching pack with Python 3.10+ (standard library only)."""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEED = 20261011
HEADERS = ["order_id", "order_date", "region", "channel", "product_id", "units", "unit_price_usd", "discount_rate", "status"]
PRODUCTS = [
    ["P001", "A5 notebook", "Office", "4.50"],
    ["P002", "Gel pen pack", "Office", "6.25"],
    ["P003", "Desk organiser", "Office", "18.40"],
    ["P004", "USB cable", "Accessories", "9.90"],
    ["P005", "Water bottle", "Drinkware", "22.75"],
    ["P006", "Canvas tote", "Accessories", "14.60"],
]
REGIONS = ["North", "South", "East", "West"]
CHANNELS = ["Online", "Retail", "Wholesale"]
DISCOUNTS = ["0.00", "0.05", "0.10", "0.15"]


def write_csv(name, headers, rows):
    with (ROOT / name).open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(headers)
        writer.writerows(rows)


def net(row):
    if row[8] != "Completed":
        return Decimal("0.00")
    return (Decimal(row[5]) * Decimal(row[6]) * (1 - Decimal(row[7]))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def build():
    ROOT.mkdir(parents=True, exist_ok=True)
    state = SEED

    def draw(limit):
        nonlocal state
        state = (1664525 * state + 1013904223) % 2**32
        # Use high bits rather than the poorly mixed low bits of this teaching PRNG.
        return (state >> 8) % limit

    sales = []
    for i in range(144):
        product = PRODUCTS[draw(len(PRODUCTS))]
        region, channel = REGIONS[draw(4)], CHANNELS[draw(3)]
        units, discount = str(1 + draw(8)), DISCOUNTS[draw(4)]
        status = ["Cancelled", "Returned"] [draw(2)] if draw(10) < 2 else "Completed"
        sales.append([f"ORD-{i + 1:04}", (date(2026, 1, 1) + timedelta(days=i * 89 // 143)).isoformat(), region, channel, product[0], units, product[3], discount, status])

    messy = [row.copy() for row in sales]
    defects = []

    def change(number, field, raw, issue, handling):
        col = HEADERS.index(field)
        expected = messy[number - 1][col]
        messy[number - 1][col] = raw
        defects.append([f"ORD-{number:04}", field, issue, raw, expected, handling])

    for number in [7, 31, 64, 102, 133]:
        change(number, "region", "  " + sales[number - 1][2] + "  ", "ascii_spaces", "TRIM")
    for number in [19, 86]:
        change(number, "region", "\u00a0" + sales[number - 1][2] + "\u00a0", "nonbreaking_spaces", "SUBSTITUTE CHAR(160), then TRIM")
    for number in [11, 48, 109]:
        change(number, "channel", sales[number - 1][3].lower(), "lowercase_category", "PROPER after TRIM")
    for number in [21, 98]:
        change(number, "product_id", " " + sales[number - 1][4] + " ", "ascii_spaces", "TRIM")
    for number in [24, 78, 124]:
        change(number, "units", "  " + sales[number - 1][5] + "  ", "padded_number", "VALUE after TRIM")
    for number in [29, 93, 138]:
        change(number, "unit_price_usd", "$" + sales[number - 1][6], "currency_symbol", "SUBSTITUTE dollar sign, then VALUE")
    for number in [34, 112]:
        change(number, "discount_rate", str(int(Decimal(sales[number - 1][7]) * 100)) + "%", "percent_text", "Remove percent sign, convert to number, divide by 100")
    for number in [13, 87, 140]:
        change(number, "order_date", sales[number - 1][1].replace("-", "/"), "year_first_slashes", "Parse explicitly as YYYY/MM/DD")
    for number in [18, 52, 116]:
        change(number, "order_date", date.fromisoformat(sales[number - 1][1]).strftime("%d/%m/%Y"), "day_first_slashes", "Parse explicitly as DD/MM/YYYY, never infer locale")
    change(44, "region", "", "missing_required_value", "Flag missing. Instructor ground truth needed.")
    change(67, "units", "", "missing_required_value", "Flag missing. Do not replace with zero. Instructor ground truth needed.")
    change(100, "order_date", "2026-02-30", "invalid_calendar_date", "Flag invalid. DATE rolls this forward. Instructor ground truth needed.")
    for number in [8, 38, 79, 120]:
        messy.append(messy[number - 1].copy())
        defects.append([f"ORD-{number:04}", "__row__", "duplicate_row", "second occurrence appended", "one row per order_id", "Keep first occurrence; remove later exact copy."])

    write_csv("sales.csv", HEADERS, sales)
    write_csv("messy-sales.csv", HEADERS, messy)
    write_csv("products.csv", ["product_id", "product_name", "category", "list_price_usd"], PRODUCTS)
    write_csv("defects.csv", ["order_id", "field", "defect_type", "raw_value", "expected_value", "handling"], defects)

    total = sum(map(net, sales), Decimal("0.00"))
    north_online = sum((net(r) for r in sales if r[2] == "North" and r[3] == "Online"), Decimal("0.00"))
    february = sum((net(r) for r in sales if "2026-02-01" <= r[1] < "2026-03-01"), Decimal("0.00"))
    office_ids = {p[0] for p in PRODUCTS if p[2] == "Office"}
    office = sum((net(r) for r in sales if r[4] in office_ids), Decimal("0.00"))
    returned = sum(r[8] == "Returned" for r in sales)
    completed = sum(r[8] == "Completed" for r in sales)
    answers = [
        ["01", "row_count", "144", "rows", "Header excluded"],
        ["01", "first_date", sales[0][1], "ISO date", "After explicit import"],
        ["01", "last_date", sales[-1][1], "ISO date", "After explicit import"],
        ["02", "completed_net_sales", f"{total:.2f}", "USD", "Round each completed line to cents, then sum"],
        ["02", "completed_orders", str(completed), "orders", "Returned and cancelled contribute zero"],
        ["03", "returned_orders", str(returned), "orders", "Count status, not units"],
        ["04", "north_online_net_sales", f"{north_online:.2f}", "USD", "Both criteria must match"],
        ["05", "february_net_sales", f"{february:.2f}", "USD", "2026-02-01 inclusive; 2026-03-01 exclusive"],
        ["06", "P004_product_name", "USB cable", "text", "Exact lookup"],
        ["06", "office_net_sales", f"{office:.2f}", "USD", "Lookup category from products.csv"],
        ["06", "unmatched_products", "0", "orders", "Sales keys all exist in product table"],
        ["07", "region_cells_changed", "7", "cells", "Five ASCII-space and two NBSP cells"],
        ["07", "region_cells_missing", "1", "cells", "Keep unresolved missing value visible"],
        ["08", "extra_duplicate_rows", "4", "rows", "Later occurrences only; eight rows belong to duplicate pairs"],
        ["08", "distinct_order_ids", "144", "IDs", "148 raw rows less four repeated occurrences"],
        ["09", "invalid_calendar_dates", "1", "rows", "ORD-0100, 2026-02-30"],
        ["09", "valid_date_rows_before_dedup", "147", "rows", "Includes four duplicate rows"],
        ["10", "missing_required_fields", "2", "cells", "ORD-0044 region; ORD-0067 units"],
        ["10", "irrecoverable_fields", "3", "cells", "Two missing fields and one invalid date need supplied ground truth"],
        ["10", "reconciled_rows", "144", "rows", "After documented normalisation, deduplication and ground-truth repairs"],
        ["10", "reconciled_net_sales", f"{total:.2f}", "USD", "Must agree with clean control"],
    ]
    write_csv("answers.csv", ["exercise_id", "metric", "value", "unit", "notes"], answers)

    descriptions = {
        "order_id": ("string", "Stable synthetic transaction ID. Each order contains exactly one product line.", "Unique in sales.csv; duplicates intentional in messy-sales.csv"),
        "order_date": ("date", "Calendar date of the synthetic order, 2026-01-01 through 2026-03-31.", "Clean: YYYY-MM-DD. Messy: also YYYY/MM/DD and explicitly DD/MM/YYYY; one invalid date"),
        "region": ("string", "Fictional shop reporting region, not a customer's location.", "North; South; East; West. Messy: spaces, NBSP and one missing value"),
        "channel": ("string", "Order channel.", "Online; Retail; Wholesale. Messy: three lowercase labels"),
        "product_id": ("string", "Lookup key into products.csv.", "P001 through P006. Messy: two padded keys"),
        "units": ("integer", "Units on one order line, including returned or cancelled orders.", "1 through 8. Messy: three padded values and one missing value"),
        "unit_price_usd": ("number", "Selling price before discount, in USD per unit, equal to catalog list price.", "Two decimal places; no tax or shipping. Messy: three dollar-sign prefixes"),
        "discount_rate": ("number", "Fraction of the pre-discount line amount removed.", "0.00; 0.05; 0.10; 0.15. Messy: two percent strings"),
        "status": ("string", "Teaching convention: only Completed orders contribute to net sales.", "Completed; Returned; Cancelled. No negative return transaction is modelled"),
    }
    dictionary = []
    for resource in ["sales", "messy-sales"]:
        for col, field in enumerate(HEADERS):
            typ, description, rules = descriptions[field]
            dictionary.append([resource, field, "string" if resource == "messy-sales" else typ, description, "USD" if field == "unit_price_usd" else "", rules, (sales if resource == "sales" else messy)[0][col]])
    for field, typ, description, unit, rules, example in [
        ["product_id", "string", "Unique catalog product key.", "", "P001 through P006", "P001"],
        ["product_name", "string", "Fictional product label.", "", "No manufacturer or trademark claims", "A5 notebook"],
        ["category", "string", "Category used for a keyed lookup exercise.", "", "Office; Accessories; Drinkware", "Office"],
        ["list_price_usd", "number", "Catalog price before discount, equal to sales unit price.", "USD per unit", "Positive, two decimal places", "4.50"],
    ]:
        dictionary.append(["products", field, typ, description, unit, rules, example])
    write_csv("dictionary.csv", ["resource", "field", "logical_type", "description", "unit", "rules", "example"], dictionary)

    def field(name, typ="string", **constraints):
        result = {"name": name, "type": typ}
        if constraints:
            result["constraints"] = constraints
        return result

    sales_fields = [field("order_id", required=True, pattern="^ORD-[0-9]{4}$"), field("order_date", "date", required=True), field("region", required=True, enum=REGIONS), field("channel", required=True, enum=CHANNELS), field("product_id", required=True), field("units", "integer", required=True, minimum=1, maximum=8), field("unit_price_usd", "number", required=True, minimum=0), field("discount_rate", "number", required=True, minimum=0, maximum=1), field("status", required=True, enum=["Completed", "Returned", "Cancelled"])]

    def resource(name, headers, fields=None, **schema_extra):
        schema = {"fields": fields or [field(h) for h in headers], "missingValues": [""]}
        schema.update(schema_extra)
        return {"name": name, "path": name + ".csv", "profile": "tabular-data-resource", "format": "csv", "mediatype": "text/csv", "encoding": "utf-8", "dialect": {"delimiter": ",", "quoteChar": "\"", "header": True}, "schema": schema}

    metadata = {
        "profile": "tabular-data-package", "name": "synthetic-shop-sales-spreadsheet-practice", "title": "Synthetic Shop Sales: Spreadsheet Import and Cleaning Practice", "version": "1.0.0",
        "description": "Original synthetic teaching data: 144 one-product transactions from January to March 2026, a deliberately defective 148-row companion, a six-product lookup table, ten Excel/Google Sheets exercises and independently checkable answer controls. No real people or real transactions. See README.md for provenance and import rules.",
        "created": "2026-10-11T00:00:00Z", "keywords": ["synthetic-data", "spreadsheet", "excel", "google-sheets", "csv", "data-cleaning", "education"],
        "licenses": [{"name": "CC0-1.0", "title": "CC0 1.0 Universal", "path": "https://creativecommons.org/publicdomain/zero/1.0/"}],
        "sources": [{"title": "Original data generated by generate.py in this package", "path": "generate.py"}],
        "contributors": [{"title": "FormulaSmith project", "role": "publisher"}],
        "resources": [
            resource("sales", HEADERS, sales_fields, primaryKey="order_id", foreignKeys=[{"fields": "product_id", "reference": {"resource": "products", "fields": "product_id"}}]),
            resource("messy-sales", HEADERS),
            resource("products", ["product_id", "product_name", "category", "list_price_usd"], [field("product_id", required=True), field("product_name", required=True), field("category", required=True), field("list_price_usd", "number", required=True, minimum=0)], primaryKey="product_id"),
            resource("dictionary", ["resource", "field", "logical_type", "description", "unit", "rules", "example"]),
            resource("answers", ["exercise_id", "metric", "value", "unit", "notes"]),
            resource("defects", ["order_id", "field", "defect_type", "raw_value", "expected_value", "handling"]),
        ],
        "synthetic": True,
    }
    (ROOT / "datapackage.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    (ROOT / "README.md").write_text(f"""# Synthetic Shop Sales: Spreadsheet Import and Cleaning Practice

A small fictional stationery and accessories shop needs a quarterly sales summary. First import its clean orders, calculate completed-order sales and join a product catalog. Then repair a second export with realistic whitespace, typing, date and duplicate problems.

This pack contains **144 original synthetic transactions**, **148 deliberately messy rows**, **6 products** and **10 exercises**. Every order is one product line, so `order_id` is the clean table's primary key. Dates span 1 January to 31 March 2026. No real people, customers, companies or transactions are represented. Values are teaching examples, not evidence about market demand or business performance.

## Start here

1. Import `sales.csv` on a sheet named `Sales` and `products.csv` on `Products`. Put headers in row 1. Use comma as the delimiter, UTF-8, a period as the decimal separator and English formula names. In Google Sheets set File > Settings > Locale to United States before importing and using VALUE. In Excel Power Query use a dot-decimal locale, such as English (United States), for numeric conversion; if the workbook's VALUE function expects comma decimals, normalize numeric text using the matching locale or Excel NUMBERVALUE with an explicit period decimal separator. Changing formula argument separators alone does not change numeric parsing. Prices are USD; `0.10` is a 10% discount. Import order/product IDs as text and units/prices/discounts as numbers.
2. Follow `exercises.md`. It specifies date conversion rather than relying on a machine's locale. Formulas use commas; locales using semicolons may require separator changes. Excel for Microsoft 365 and Google Sheets are the target engines. Exact-match VLOOKUP alternatives are included for older Excel.
3. Import **all columns of `messy-sales.csv` as text** on `Messy` to preserve the intended problems. In Excel use Data > From Text/CSV > Transform Data, remove automatic Changed Type if present and set all columns to Text. In Sheets use File > Import and turn off **Convert text to numbers, dates, and formulas**. Opening a CSV by double-click can silently convert dates and lose this lesson.
4. Check your results against `answers.csv` and `solutions.md`. Instructors can withhold those files, `defects.csv` and `sales.csv` during the cleaning section.

## Files

| File | Purpose |
|---|---|
| `sales.csv` | Clean ground truth, 144 rows and 9 fields |
| `messy-sales.csv` | Same orders with documented defects and four appended duplicate rows |
| `products.csv` | Six-row product/category/price lookup table |
| `dictionary.csv` | Field meanings, units and clean/messy typing rules |
| `exercises.md` | Ten practical tasks with explicit ranges and import assumptions |
| `answers.csv`, `solutions.md` | Numerical controls and worked formulas |
| `defects.csv` | Instructor manifest of every introduced cell or row defect |
| `datapackage.json` | DataHub-compatible resource metadata and table schemas |
| `generate.py` | Deterministic standard-library generator for all data and teaching documents |
| `verify.py` | Independent standard-library validation of the saved files and answer controls |
| `independent-checks.json` | Saved report from the independent verifier |
| `spreadsheet-checks.json` | Formula evaluation evidence from the local spreadsheet calculation engine |
| `LICENSE.md` | CC0 1.0 public-domain dedication for this pack |

## Calculation convention

For a Completed order, net sales are `ROUND(units * unit_price_usd * (1 - discount_rate), 2)`. Returned and Cancelled orders contribute zero. Round each line to cents before summing. The worked solution uses integer price cents and whole-percent discounts, then rounds to the nearest cent before converting back to USD. This avoids binary floating-point noise at half-cent boundaries for this dataset. This simple convention excludes taxes, shipping, payments, return cash flows and costs. It is not an accounting model.

Clean controls: {completed} Completed orders, {returned} Returned orders and **USD {total:.2f}** completed net sales. Expected North/Online sales are USD {north_online:.2f}; February sales are USD {february:.2f}.

## Intentional defects

There are {len(defects) - 4} altered cells and four appended exact-copy rows. The manifest identifies five region cells with ASCII padding, two with nonbreaking spaces (U+00A0), three lowercase channels, two padded product keys, three padded unit counts, three dollar-prefixed prices, two percent strings, three YYYY/MM/DD dates, three explicitly DD/MM/YYYY dates, two missing required values and one impossible date (`2026-02-30`). Groups use different orders. Four unchanged orders are repeated at the end.

Two missing values and the impossible date cannot be recovered from the defective export alone. Flag them for review. The supplied clean table provides ground truth for this exercise; real data would require a source-system correction. Do not guess or turn missing units into zero. The messy schema intentionally treats fields as strings and has no unique primary-key constraint.

## Provenance and reproduction

Created on 11 October 2026 for this teaching pack. `generate.py` creates these rows from a fixed seed ({SEED}) using a documented integer generator; it does not download or copy any external dataset. Run `python generate.py` followed by `python verify.py` with Python 3.10 or later. The generator rewrites the six CSV files, Markdown teaching documents, metadata and `checksums.sha256` in this folder. The independent verifier reads the saved files, checks the answer controls and reconciles the defective export. CSV files use UTF-8 without a BOM, LF line endings and standard CSV quoting. Preserve IDs when sorting and compare rows by ID, not their current positions.

The pack is prepared by the FormulaSmith project. Related learning resource: [FormulaSmith sample-data library](https://formulasmith.com/en/sample-data/). This resource is affiliated with the publisher; it is not the source of the original generated rows above.

## Licence

The original data, teaching documents and scripts in this pack are dedicated to the public domain under **CC0 1.0 Universal**. See `LICENSE.md` for the dedication and legal-code link. Attribution is appreciated but is not a condition of reuse.
""", encoding="utf-8")

    (ROOT / "exercises.md").write_text("""# Ten spreadsheet exercises

Use `Sales!A1:I145`, `Products!A1:D7` and `Messy!A1:I149`. Headers count as row 1. Do not add totals inside the source ranges. Work on copies and keep original raw values. Formulas below use English names and comma separators.

1. **Import and validate dates.** Import the clean files using the README rules. In Sales K1 enter `parsed_date`. Convert every Sales B date into a real spreadsheet date in K, whether B arrived as text or a date serial. Verify that K is numeric, then report the record count, minimum date and maximum date. Display dates as `yyyy-mm-dd`. Do not use DATEVALUE with an unspecified locale.
2. **Calculate completed net sales.** In Sales J1 enter `net_sales_usd`. In M and N create integer unit-price cents and whole discount percentages from G and H. Use those helpers to calculate one amount per order in J using the stated status and line-rounding convention. Return the total net sales and the count of Completed orders. Explain why returned and cancelled units do not belong in the completed-sales amount.
3. **Count returns with COUNTIF.** How many orders have status Returned? Count orders, not units, and use a bounded source range. Check that Completed + Returned + Cancelled counts equal the clean record count.
4. **Apply two SUMIFS criteria.** What is net sales for orders in the North region and Online channel? Include both conditions in the same formula and sum the net column from exercise 2.
5. **Use date boundaries in SUMIFS.** What is February 2026 net sales? Use K's numeric dates from exercise 1, with a start date inclusive and the next month's first day exclusive. Explain why filtering by the text “February” is unreliable.
6. **Join the catalog by an exact key.** Return P004's product name. Then add category in Sales L using product_id and the Products lookup table. Flag missing matches as `Unmapped`, count them and calculate net sales for the Office category. Do not assume either table is sorted the same way.
7. **Clean invisible spaces.** On Messy J1 enter `clean_region`. Use TRIM and SUBSTITUTE with CHAR(160) so both ordinary spaces and nonbreaking spaces are removed. In K compare raw C with cleaned J using EXACT, returning 1 when changed and 0 otherwise. How many cells change? How many regions remain missing? Never invent a replacement region.
8. **Find extra duplicate occurrences.** On Messy L1 enter `duplicate_after_first`. Flag an order ID with 1 only when it has appeared earlier in column A, and 0 otherwise. Count the extra rows and the distinct IDs. Explain why testing COUNTIF across the full column > 1 counts eight affected rows rather than the four extra copies. Remove later copies only after confirming their other fields agree.
9. **Import mixed dates without guessing.** On Messy M:P create year, month, day and candidate date. Raw B contains YYYY-MM-DD, YYYY/MM/DD and DD/MM/YYYY; all slash dates with the year at the end are explicitly day-first. In Q create `valid_date`, returning 1 for valid and 0 for invalid, by comparing the candidate's YEAR, MONTH and DAY back to the extracted parts. Count invalid dates and valid raw rows before deduplication. Why is DATE alone insufficient for `2026-02-30`?
10. **Reconcile the cleaned export.** Make a separate Cleaned sheet. Normalize channel case, trim product IDs, convert padded units, remove the dollar prefix from prices and convert percent-text discounts. Preserve missing values as missing; flag the impossible date. Before using ground truth, report the number of missing required cells and the number of irrecoverable cells including invalid dates. Use the supplied clean record for only those three cells, record the repairs and remove the four later duplicate copies. Compare all nine fields by order_id with sales.csv. Recompute net sales and confirm the clean row count and total from exercise 2. A matching total alone does not prove each record is correct.
""", encoding="utf-8")

    (ROOT / "solutions.md").write_text(f"""# Worked solutions

These solutions refer to the sheet layout in `exercises.md`. Fill row formulas down to row 145 on Sales or row 149 on Messy. Formula examples use English function names and commas. Import numeric clean columns using a period decimal separator. There is no CSV formula code in the source data.

## 1. Clean import and dates

Sales K2: `=IF(ISNUMBER(B2),B2,DATE(VALUE(LEFT(B2,4)),VALUE(MID(B2,6,2)),VALUE(RIGHT(B2,2))))`

Use `=COUNTA(A2:A145)` for **144** records, `=COUNT(K2:K145)` for **144** numeric dates, `=MIN(K2:K145)` for **2026-01-01** and `=MAX(K2:K145)` for **2026-03-31**. Format K and the minimum/maximum result cells as dates. These checks use the clean file; exercise 9 adds calendar validation for defective dates.

## 2. Completed net sales

Sales M1: `unit_price_cents`; M2: `=ROUND(G2*100,0)`.

Sales N1: `discount_percent`; N2: `=ROUND(H2*100,0)`.

Sales J2: `=IF(I2="Completed",ROUND(F2*M2*(100-N2)/100,0)/100,0)`

`=SUM(J2:J145)` gives **USD {total:.2f}**. `=COUNTIF(I2:I145,"Completed")` gives **{completed}**. Fill both helpers before the net formula. All prices have two decimals and discounts are whole percentages, so integer cents make this dataset's half-cent rounding explicit and avoid floating-point boundary differences. For example, ORD-0070 is exactly USD129.675 before rounding and USD129.68 after rounding. A different dataset with fractional-cent prices or fractional-percent discounts needs a revised precision policy. Returned and Cancelled rows contribute zero under this pack's explicit convention.

## 3. Returned orders

`=COUNTIF(Sales!I2:I145,"Returned")` gives **{returned}** orders. The three status counts sum to 144. Counting F's units would answer a different question.

## 4. North and Online

`=SUMIFS(Sales!J2:J145,Sales!C2:C145,"North",Sales!D2:D145,"Online")` gives **USD {north_online:.2f}**. The criteria are combined with AND.

## 5. February

`=SUMIFS(Sales!J2:J145,Sales!K2:K145,">="&DATE(2026,2,1),Sales!K2:K145,"<"&DATE(2026,3,1))` gives **USD {february:.2f}**. K must hold numeric dates, not date-looking text. The exclusive March boundary also works if the source is later extended to timestamps.

## 6. Exact catalog lookup

`=XLOOKUP("P004",Products!$A$2:$A$7,Products!$B$2:$B$7,"Unmapped",0)` returns **USB cable**. Older Excel: `=IFNA(VLOOKUP("P004",Products!$A$2:$D$7,2,FALSE),"Unmapped")`.

Sales L2: `=XLOOKUP(E2,Products!$A$2:$A$7,Products!$C$2:$C$7,"Unmapped",0)`

Older Excel: `=IFNA(VLOOKUP(E2,Products!$A$2:$D$7,3,FALSE),"Unmapped")`. `=COUNTIF(L2:L145,"Unmapped")` is **0**. `=SUMIFS(J2:J145,L2:L145,"Office")` gives **USD {office:.2f}**. Validate uniqueness of Products' six keys first. A first-match lookup cannot safely resolve conflicting duplicate catalog keys.

## 7. Whitespace

Messy J2: `=TRIM(SUBSTITUTE(C2,CHAR(160)," "))`

Messy K2: `=IF(EXACT(C2,J2),0,1)`. `=COUNTIF(K2:K149,1)` gives **7** changed cells. `=COUNTBLANK(J2:J149)` gives **1** unresolved region. TRIM by itself does not remove a nonbreaking space. The blank is ORD-0044 and must remain visible.

## 8. Duplicate occurrences

Messy L2: `=IF(COUNTIF($A$2:A2,A2)>1,1,0)`

`=COUNTIF(L2:L149,1)` gives **4** extra rows. `=COUNTA(A2:A149)-COUNTIF(L2:L149,1)` gives **144** distinct IDs because there are no blank IDs. Appended copies are ORD-0008, ORD-0038, ORD-0079 and ORD-0120. A whole-range `COUNTIF($A$2:$A$149,A2)>1` flags both copies, giving eight affected rows. Check all fields agree before keeping the first.

## 9. Mixed dates and impossible days

The following works on the raw text-preserving import. Four-digit years always occur at one end of the ten-character input. YYYY/MM/DD and YYYY-MM-DD use the same substring positions.

Messy M2 (year): `=IF(OR(MID(B2,5,1)="-",MID(B2,5,1)="/"),VALUE(LEFT(B2,4)),VALUE(RIGHT(B2,4)))`

Messy N2 (month): `=IF(OR(MID(B2,5,1)="-",MID(B2,5,1)="/"),VALUE(MID(B2,6,2)),VALUE(MID(B2,4,2)))`

Messy O2 (day): `=IF(OR(MID(B2,5,1)="-",MID(B2,5,1)="/"),VALUE(RIGHT(B2,2)),VALUE(LEFT(B2,2)))`

Messy P2 (candidate): `=DATE(M2,N2,O2)`

Messy Q2 (valid): `=IF(AND(YEAR(P2)=M2,MONTH(P2)=N2,DAY(P2)=O2),1,0)`

`=COUNTIF(Q2:Q149,0)` gives **1** invalid date; `=COUNTIF(Q2:Q149,1)` gives **147** valid raw rows including duplicates. ORD-0100 contains `2026-02-30`. DATE silently normalizes it into March, so the round-trip validation is necessary. These fixed-position formulas are for the documented ten-character formats; unexpected formats should be flagged separately.

## 10. Clean and reconcile

Use the prior region/date helpers. Useful normalization formulas on a row copied from Messy are:

| Field | Formula using raw row 2 |
|---|---|
| channel | `=PROPER(TRIM(Messy!D2))` |
| product_id | `=TRIM(Messy!E2)` |
| units | `=IF(TRIM(Messy!F2)="","Missing",VALUE(TRIM(Messy!F2)))` |
| unit_price_usd | `=VALUE(SUBSTITUTE(TRIM(Messy!G2),"$",""))` |
| discount_rate | `=IF(RIGHT(TRIM(Messy!H2),1)="%",VALUE(SUBSTITUTE(TRIM(Messy!H2),"%",""))/100,VALUE(TRIM(Messy!H2)))` |

For these files, `=COUNTBLANK(Messy!C2:C149)+COUNTBLANK(Messy!F2:F149)` gives **2** missing required cells. Together with the invalid date there are **3** irrecoverable cells. This targeted count is valid because `defects.csv` specifies which required fields can be missing; a general import pipeline should check every required field.

Repair only ORD-0044 region (**{sales[43][2]}**), ORD-0067 units (**{sales[66][5]}**) and ORD-0100 date (**{sales[99][1]}**) from the provided ground truth, and log those corrections. Remove four later duplicate rows and order the remaining data by order_id. Reconcile exactly **144** IDs and all nine fields against sales.csv, allowing equivalent typed numeric/date representations. Recomputed completed net sales must be **USD {total:.2f}**. Compare record-level fields and status counts as well as totals.

The standard-library generator computes cents using Decimal with half-up rounding. The companion verification script checks the saved CSVs independently. The local spreadsheet-engine checks evaluate the formulas for import, totals, filtered sales, exact lookup, whitespace, duplicates and date validation. Native Excel/Google Sheets execution is a separate check; imported types and locale still matter.
""", encoding="utf-8")

    (ROOT / "LICENSE.md").write_text("""# CC0 1.0 Universal

To the extent possible under law, the FormulaSmith project has waived all copyright and related or neighboring rights to the original data, teaching documents and scripts in Synthetic Shop Sales: Spreadsheet Import and Cleaning Practice, under the CC0 1.0 Universal public-domain dedication.

The work is provided without warranties. You may copy, modify and redistribute it, including for commercial purposes. Attribution is appreciated but is not a condition of reuse.

CC0 legal code: https://creativecommons.org/publicdomain/zero/1.0/legalcode
""", encoding="utf-8")
    names = ["sales.csv", "messy-sales.csv", "products.csv", "dictionary.csv", "answers.csv", "defects.csv", "README.md", "exercises.md", "solutions.md", "datapackage.json", "generate.py", "LICENSE.md"]
    if (ROOT / "verify.py").exists():
        names.append("verify.py")
    (ROOT / "checksums.sha256").write_text("".join(f"{hashlib.sha256((ROOT / name).read_bytes()).hexdigest()}  {name}\n" for name in names), encoding="utf-8")
    print(json.dumps({"sales_rows": len(sales), "messy_rows": len(messy), "products": len(PRODUCTS), "altered_cells": len(defects)-4, "duplicate_rows": 4, "net_sales_usd": str(total), "completed_orders": completed, "returned_orders": returned}, indent=2))


if __name__ == "__main__":
    build()
