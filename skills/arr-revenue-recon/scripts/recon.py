#!/usr/bin/env python3
"""ARR by customer vs annualized monthly GAAP revenue by customer.

Usage:
  python3 recon.py ARR.csv REVENUE.csv --month 2026-10 [--threshold-pct 10] [--out-csv recon.csv]
           [--arr-customer-col customer] [--arr-col arr] [--rev-customer-col customer] [--rev-col gaap_revenue]

Annualized revenue = monthly GAAP revenue x 12.
Variance % = (annualized revenue - ARR) / ARR.
Status:
  INVESTIGATE   |variance %| > threshold
  ARR ONLY      ARR > 0 but no revenue this month (not started? churned? missing invoice?)
  REVENUE ONLY  revenue this month but no ARR (one-time / services? missing from ARR schedule?)
  OK            within threshold
Customer names are matched after normalizing case, punctuation, and suffixes (Inc, LLC, Ltd, Corp, Co).
"""
import argparse
import csv
import re
import sys

SUFFIX = re.compile(r"\b(incorporated|inc|llc|ltd|limited|corp|corporation|co|company|plc|gmbh)\b")


def norm(name):
    s = re.sub(r"[^a-z0-9 ]", " ", name.lower())
    s = SUFFIX.sub(" ", s)
    return " ".join(s.split())


def money(v):
    v = (v or "").strip().replace("$", "").replace(",", "")
    if v.startswith("(") and v.endswith(")"):
        v = "-" + v[1:-1]
    return float(v) if v not in ("", "-") else 0.0


def load(path, ccol, vcol):
    out, names = {}, {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        sys.exit(f"{path}: no rows")
    cols = {c.strip().lower(): c for c in rows[0].keys()}
    if ccol.lower() not in cols or vcol.lower() not in cols:
        sys.exit(f"{path}: need columns '{ccol}' and '{vcol}', found {list(rows[0].keys())}")
    for r in rows:
        name = (r[cols[ccol.lower()]] or "").strip()
        if not name or name.lower() == "total":
            continue
        k = norm(name)
        out[k] = out.get(k, 0.0) + money(r[cols[vcol.lower()]])
        names.setdefault(k, name)
    return out, names


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("arr")
    ap.add_argument("revenue")
    ap.add_argument("--month", required=True)
    ap.add_argument("--threshold-pct", type=float, default=10.0)
    ap.add_argument("--out-csv")
    ap.add_argument("--arr-customer-col", default="customer")
    ap.add_argument("--arr-col", default="arr")
    ap.add_argument("--rev-customer-col", default="customer")
    ap.add_argument("--rev-col", default="gaap_revenue")
    a = ap.parse_args()

    arr, an = load(a.arr, a.arr_customer_col, a.arr_col)
    rev, rn = load(a.revenue, a.rev_customer_col, a.rev_col)
    rows = []
    for k in sorted(set(arr) | set(rev)):
        A, M = arr.get(k, 0.0), rev.get(k, 0.0)
        ann = M * 12
        var = ann - A
        pct = var / A * 100 if A else None
        if A and not M:
            status = "ARR ONLY"
        elif M and not A:
            status = "REVENUE ONLY"
        elif pct is not None and abs(pct) > a.threshold_pct:
            status = "INVESTIGATE"
        else:
            status = "OK"
        names = {an.get(k), rn.get(k)} - {None}
        rows.append({"customer": an.get(k) or rn.get(k), "name_variants": " / ".join(sorted(names)) if len(names) > 1 else "",
                     "arr": round(A, 2), "monthly_gaap_revenue": round(M, 2), "annualized_revenue": round(ann, 2),
                     "variance": round(var, 2), "variance_pct": "" if pct is None else round(pct, 1), "status": status})

    order = {"INVESTIGATE": 0, "ARR ONLY": 1, "REVENUE ONLY": 2, "OK": 3}
    rows.sort(key=lambda r: (order[r["status"]], -abs(r["variance"])))
    if a.out_csv:
        with open(a.out_csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

    tA = sum(arr.values()); tM = sum(rev.values())
    flagged = [r for r in rows if r["status"] != "OK"]
    print(f"### ARR vs annualized GAAP revenue — {a.month}")
    print(f"Customers: {len(rows)} | Flagged: {len(flagged)} (threshold ±{a.threshold_pct:g}%)")
    print(f"Total ARR {tA:,.0f} | Monthly GAAP revenue {tM:,.0f} | Annualized {tM*12:,.0f} | "
          f"Gap {tM*12 - tA:+,.0f} ({(tM*12/tA - 1)*100 if tA else 0:+.1f}%)\n")
    print("| Customer | Status | ARR | Monthly rev | Annualized | Gap | Gap % |")
    print("|---|---|---|---|---|---|---|")
    for r in flagged:
        pct = "n/a" if r["variance_pct"] == "" else f"{r['variance_pct']:+.1f}%"
        print(f"| {r['customer']} | {r['status']} | {r['arr']:,.0f} | {r['monthly_gaap_revenue']:,.0f} | "
              f"{r['annualized_revenue']:,.0f} | {r['variance']:+,.0f} | {pct} |")
    merged = [r for r in rows if r["name_variants"]]
    if merged:
        print("\nName matches to confirm: " + "; ".join(r["name_variants"] for r in merged))


if __name__ == "__main__":
    main()
