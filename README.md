# Synthetic Shop Sales: Spreadsheet Import and Cleaning Practice

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

Clean controls: 114 Completed orders, 11 Returned orders and **USD 6136.66** completed net sales. Expected North/Online sales are USD 340.73; February sales are USD 1786.52.

## Intentional defects

There are 29 altered cells and four appended exact-copy rows. The manifest identifies five region cells with ASCII padding, two with nonbreaking spaces (U+00A0), three lowercase channels, two padded product keys, three padded unit counts, three dollar-prefixed prices, two percent strings, three YYYY/MM/DD dates, three explicitly DD/MM/YYYY dates, two missing required values and one impossible date (`2026-02-30`). Groups use different orders. Four unchanged orders are repeated at the end.

Two missing values and the impossible date cannot be recovered from the defective export alone. Flag them for review. The supplied clean table provides ground truth for this exercise; real data would require a source-system correction. Do not guess or turn missing units into zero. The messy schema intentionally treats fields as strings and has no unique primary-key constraint.

## Provenance and reproduction

Created on 11 October 2026 for this teaching pack. `generate.py` creates these rows from a fixed seed (20261011) using a documented integer generator; it does not download or copy any external dataset. Run `python generate.py` followed by `python verify.py` with Python 3.10 or later. The generator rewrites the six CSV files, Markdown teaching documents, metadata and `checksums.sha256` in this folder. The independent verifier reads the saved files, checks the answer controls and reconciles the defective export. CSV files use UTF-8 without a BOM, LF line endings and standard CSV quoting. Preserve IDs when sorting and compare rows by ID, not their current positions.

The pack is prepared by the FormulaSmith project. Related learning resource: [FormulaSmith sample-data library](https://formulasmith.com/en/sample-data/). This resource is affiliated with the publisher; it is not the source of the original generated rows above.

## Licence

The original data, teaching documents and scripts in this pack are dedicated to the public domain under **CC0 1.0 Universal**. See `LICENSE.md` for the dedication and legal-code link. Attribution is appreciated but is not a condition of reuse.
