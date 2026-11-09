#!/usr/bin/env python3
"""Reconcile ARR by customer to annualized monthly GAAP revenue by customer.

Inputs (CSV):
  ARR file:      customer, arr                     (ARR as of month-end; extra columns ignored)
  Revenue file:  month (YYYY-MM), customer, revenue (monthly recognized GAAP revenue)
Usage:
  python3 arr_vs_revenue.py ARR.csv REVENUE.csv --month 2026-10 [--threshold 10] [--out exceptions.csv]

For each customer: annualized revenue = revenue[month] x 12; gap = ARR - annualized;
gap % = gap / ARR. Customers with |gap %| > threshold (or present in only one file) are flagged
for investigation, with a likely-driver hint based on the prior month's revenue.
"""
import argparse
import csv
from collections import defaultdict


def prev_month(ym):
    y, m = map(int, ym.split("-"))
    return f"{y - 1}-12" if m == 1 else f"{y}-{m - 1:02d}"


def num(v):
    try:
        return float(str(v).replace(",", "").replace("$", "")) if str(v).strip() else 0.0
    except ValueError:
        return 0.0


def hint(arr, rev, rev_prior, has_prior=True):
    run_rate = arr / 12 if arr else 0
    if not has_prior:  # no prior month to compare against: list candidates only
        if arr and not rev:
            return "No revenue this month: go-live delay, revenue held (acceptance), or churned customer still in ARR"
        if rev and not arr:
            return "Revenue with no ARR: services/one-time fees, usage not in ARR, or missing from ARR file"
        if rev > run_rate:
            return "Revenue above ARR run-rate: one-time/services fees, usage overage, catch-up entry, or ARR understated"
        return "Revenue below ARR run-rate: partial-month start, ramp, credit/concession, or ARR overstated"
    if arr and not rev:
        if rev_prior:
            return "Revenue stopped this month: churned/cancelled customer still in ARR, or revenue held/reversed"
        return "No revenue yet: start-date/go-live delay or revenue held pending acceptance (booked ARR not yet live)"
    if rev and not arr:
        return "Revenue with no ARR: services/one-time fees, usage not in ARR, churned customer's trailing revenue, or missing from ARR file"
    if rev > run_rate:
        if rev_prior and abs(rev_prior - run_rate) <= 0.1 * run_rate:
            return "Revenue above run-rate this month only: one-time/services fees, overage, or catch-up/true-up entry"
        return "Revenue persistently above ARR: usage/overage or services not captured in ARR, or ARR understated"
    if not rev_prior:
        return "Revenue below run-rate, first month billed: likely partial-month (mid-month) start"
    if rev_prior and rev < 0.9 * rev_prior:
        return "Revenue dropped vs prior month: credit/concession, downgrade not yet in ARR, or revenue reversal"
    return "Revenue persistently below ARR: ramp deal, free months, discount not reflected in ARR, or ARR overstated"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("arr")
    ap.add_argument("revenue")
    ap.add_argument("--month", help="YYYY-MM; required if the revenue file has a month column with several months")
    ap.add_argument("--prior-revenue", help="optional prior-month revenue CSV (customer, revenue) when the revenue file holds one month only")
    ap.add_argument("--threshold", type=float, default=10.0, help="flag if |gap %%| exceeds this")
    ap.add_argument("--out", help="write flagged customers to this CSV")
    a = ap.parse_args()

    arr = defaultdict(float)
    with open(a.arr, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            arr[r["customer"].strip()] += num(r["arr"])
    rev, rev_prior = defaultdict(float), defaultdict(float)
    with open(a.revenue, newline="", encoding="utf-8-sig") as f:
        rdr = csv.DictReader(f)
        rows_in = list(rdr)
    if rows_in and "month" in rows_in[0]:
        months_seen = sorted({r["month"] for r in rows_in})
        if not a.month:
            a.month = months_seen[-1]
        if a.month not in months_seen:
            raise SystemExit(f"revenue file has no rows for {a.month}; months found: {months_seen}")
        pm = prev_month(a.month)
        for r in rows_in:
            if r["month"] == a.month:
                rev[r["customer"].strip()] += num(r["revenue"])
            elif r["month"] == pm:
                rev_prior[r["customer"].strip()] += num(r["revenue"])
    else:  # single-month file (folder-per-month layout)
        a.month = a.month or "latest month"
        for r in rows_in:
            rev[r["customer"].strip()] += num(r["revenue"])
    if a.prior_revenue:
        with open(a.prior_revenue, newline="", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                rev_prior[r["customer"].strip()] += num(r["revenue"])

    has_prior = bool(rev_prior)
    rows = []
    for c in sorted(set(arr) | set(rev)):
        A, R, P = arr.get(c, 0.0), rev.get(c, 0.0), rev_prior.get(c, 0.0)
        ann = R * 12
        gap = A - ann
        pct = (gap / A * 100) if A else None
        flagged = (pct is None and R) or (pct is not None and abs(pct) > a.threshold)
        rows.append({"customer": c, "arr": A, "annualized_revenue": ann, "gap": gap,
                     "gap_pct": pct, "prior_month_revenue": P, "flag": bool(flagged),
                     "likely_driver": hint(A, R, P, has_prior) if flagged else ""})

    tot_arr = sum(r["arr"] for r in rows)
    tot_ann = sum(r["annualized_revenue"] for r in rows)
    flagged = sorted([r for r in rows if r["flag"]], key=lambda r: -abs(r["gap"]))
    fmt_pct = lambda p: "n/a" if p is None else f"{p:+.1f}%"

    print(f"### ARR vs annualized GAAP revenue — {a.month}")
    print(f"Threshold: |gap| > {a.threshold:.0f}% of ARR. Annualized revenue = {a.month} revenue x 12.\n")
    print(f"- Total ARR: {tot_arr:,.0f}")
    print(f"- Total annualized revenue: {tot_ann:,.0f}")
    tp = (tot_arr - tot_ann) / tot_arr * 100 if tot_arr else 0
    print(f"- Total gap: {tot_arr - tot_ann:+,.0f} ({tp:+.1f}% of ARR)")
    print(f"- Customers: {len(rows)} | flagged: {len(flagged)} | flagged gap: {sum(r['gap'] for r in flagged):+,.0f}\n")
    print("#### Needs investigation (largest $ gap first)")
    if flagged:
        print("| Customer | ARR | Annualized rev | Gap | Gap % | Likely driver (hypothesis) |")
        print("|---|---|---|---|---|---|")
        for r in flagged:
            print(f"| {r['customer']} | {r['arr']:,.0f} | {r['annualized_revenue']:,.0f} | {r['gap']:+,.0f} | {fmt_pct(r['gap_pct'])} | {r['likely_driver']} |")
    else:
        print("None — all customers within threshold.")
    print(f"\n#### Within threshold: {len(rows) - len(flagged)} customers, gap {sum(r['gap'] for r in rows if not r['flag']):+,.0f}")

    if a.out:
        with open(a.out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            for r in flagged:
                w.writerow({**r, "gap_pct": "" if r["gap_pct"] is None else round(r["gap_pct"], 1),
                            "arr": round(r["arr"], 2), "annualized_revenue": round(r["annualized_revenue"], 2), "gap": round(r["gap"], 2)})


if __name__ == "__main__":
    main()
