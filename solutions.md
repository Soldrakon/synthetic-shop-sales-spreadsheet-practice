# Worked solutions

These solutions refer to the sheet layout in `exercises.md`. Fill row formulas down to row 145 on Sales or row 149 on Messy. Formula examples use English function names and commas. Import numeric clean columns using a period decimal separator. There is no CSV formula code in the source data.

## 1. Clean import and dates

Sales K2: `=IF(ISNUMBER(B2),B2,DATE(VALUE(LEFT(B2,4)),VALUE(MID(B2,6,2)),VALUE(RIGHT(B2,2))))`

Use `=COUNTA(A2:A145)` for **144** records, `=COUNT(K2:K145)` for **144** numeric dates, `=MIN(K2:K145)` for **2026-01-01** and `=MAX(K2:K145)` for **2026-03-31**. Format K and the minimum/maximum result cells as dates. These checks use the clean file; exercise 9 adds calendar validation for defective dates.

## 2. Completed net sales

Sales M1: `unit_price_cents`; M2: `=ROUND(G2*100,0)`.

Sales N1: `discount_percent`; N2: `=ROUND(H2*100,0)`.

Sales J2: `=IF(I2="Completed",ROUND(F2*M2*(100-N2)/100,0)/100,0)`

`=SUM(J2:J145)` gives **USD 6136.66**. `=COUNTIF(I2:I145,"Completed")` gives **114**. Fill both helpers before the net formula. All prices have two decimals and discounts are whole percentages, so integer cents make this dataset's half-cent rounding explicit and avoid floating-point boundary differences. For example, ORD-0070 is exactly USD129.675 before rounding and USD129.68 after rounding. A different dataset with fractional-cent prices or fractional-percent discounts needs a revised precision policy. Returned and Cancelled rows contribute zero under this pack's explicit convention.

## 3. Returned orders

`=COUNTIF(Sales!I2:I145,"Returned")` gives **11** orders. The three status counts sum to 144. Counting F's units would answer a different question.

## 4. North and Online

`=SUMIFS(Sales!J2:J145,Sales!C2:C145,"North",Sales!D2:D145,"Online")` gives **USD 340.73**. The criteria are combined with AND.

## 5. February

`=SUMIFS(Sales!J2:J145,Sales!K2:K145,">="&DATE(2026,2,1),Sales!K2:K145,"<"&DATE(2026,3,1))` gives **USD 1786.52**. K must hold numeric dates, not date-looking text. The exclusive March boundary also works if the source is later extended to timestamps.

## 6. Exact catalog lookup

`=XLOOKUP("P004",Products!$A$2:$A$7,Products!$B$2:$B$7,"Unmapped",0)` returns **USB cable**. Older Excel: `=IFNA(VLOOKUP("P004",Products!$A$2:$D$7,2,FALSE),"Unmapped")`.

Sales L2: `=XLOOKUP(E2,Products!$A$2:$A$7,Products!$C$2:$C$7,"Unmapped",0)`

Older Excel: `=IFNA(VLOOKUP(E2,Products!$A$2:$D$7,3,FALSE),"Unmapped")`. `=COUNTIF(L2:L145,"Unmapped")` is **0**. `=SUMIFS(J2:J145,L2:L145,"Office")` gives **USD 2178.23**. Validate uniqueness of Products' six keys first. A first-match lookup cannot safely resolve conflicting duplicate catalog keys.

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

Repair only ORD-0044 region (**East**), ORD-0067 units (**7**) and ORD-0100 date (**2026-03-03**) from the provided ground truth, and log those corrections. Remove four later duplicate rows and order the remaining data by order_id. Reconcile exactly **144** IDs and all nine fields against sales.csv, allowing equivalent typed numeric/date representations. Recomputed completed net sales must be **USD 6136.66**. Compare record-level fields and status counts as well as totals.

The standard-library generator computes cents using Decimal with half-up rounding. The companion verification script checks the saved CSVs independently. The local spreadsheet-engine checks evaluate the formulas for import, totals, filtered sales, exact lookup, whitespace, duplicates and date validation. Native Excel/Google Sheets execution is a separate check; imported types and locale still matter.
