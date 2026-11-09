#!/usr/bin/env python3
"""Driver-based consumption revenue projection with scenarios.

Input CSV columns: month, customer, segment, committed_units, consumed_units, unit_price, overage_price.
Pricing model assumed (edit to match your contracts):
  - Committed customers pay committed_units * unit_price each month (minimum), plus
    (consumed - committed) * overage_price when consumption exceeds commit.
  - Pay-as-you-go customers (committed_units = 0) pay consumed_units * overage_price.
Driver: per-customer compound monthly growth in consumption, fit on the trailing --window months.
Scenarios scale that growth: downside, base, upside.

Usage:
  python3 consumption_model.py USAGE.csv --months 3 [--window 6] [--scenarios 0.5,1.0,1.5] [--growth-cap 0.10]
Outputs a per-scenario monthly revenue table, a customer-level detail for base, and flags
(commit shortfall = possible breakage; overage run-rate = expansion signal; step-changes).
Units: currency of the price columns (sample data: $). Revenue here equals billings; see
references/asc606-notes.md for where recognition differs.
"""
import argparse
import csv
import json
import math
from collections import defaultdict


def add_months(ym, n):
    y, m = map(int, ym.split("-"))
    t = y * 12 + (m - 1) + n
    return f"{t // 12}-{t % 12 + 1:02d}"


def charge(units, commit, unit_price, overage):
    if commit > 0:
        return commit * unit_price + max(0.0, units - commit) * overage
    return units * overage


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--months", type=int, default=3)
    ap.add_argument("--window", type=int, default=6)
    ap.add_argument("--scenarios", default="0.5,1.0,1.5")
    ap.add_argument("--json")
    ap.add_argument("--growth-cap", type=float, default=0.10, help="max monthly growth used in projection")
    a = ap.parse_args()
    mults = [float(x) for x in a.scenarios.split(",")]
    names = {0: "Downside", len(mults) // 2: "Base", len(mults) - 1: "Upside"}

    cust = defaultdict(list)
    meta = {}
    with open(a.data, newline="") as fh:
        for r in csv.DictReader(fh):
            cust[r["customer"]].append((r["month"], float(r["consumed_units"])))
            meta[r["customer"]] = (r["segment"], float(r["committed_units"] or 0), float(r["unit_price"] or 0), float(r["overage_price"] or 0))

    last_month = max(m for pts in cust.values() for m, _ in pts)
    future = [add_months(last_month, i + 1) for i in range(a.months)]
    flags, detail = [], []
    scen = {mult: defaultdict(float) for mult in mults}
    actual_last = 0.0

    for c, pts in sorted(cust.items()):
        pts.sort()
        seg, commit, up, op = meta[c]
        w = pts[-a.window:]
        g = (w[-1][1] / w[0][1]) ** (1 / (len(w) - 1)) - 1 if len(w) > 1 and w[0][1] > 0 else 0.0
        g_used = min(g, a.growth_cap)
        if g > a.growth_cap:
            flags.append(f"{c}: trailing growth {g:.1%}/mo capped at {a.growth_cap:.0%} — check for step-change (launch, migration, one-off).")
        if len(pts) >= 2 and pts[-2][1] > 0 and pts[-1][1] / pts[-2][1] - 1 > 0.25:
            flags.append(f"{c}: last month consumption +{pts[-1][1] / pts[-2][1] - 1:.0%} MoM — step-change.")
        last_units = pts[-1][1]
        last_rev = charge(last_units, commit, up, op)
        actual_last += last_rev
        if commit > 0:
            util = last_units / commit
            if util < 0.85:
                flags.append(f"{c}: running at {util:.0%} of commit — shortfall/breakage and renewal-downsell risk.")
            elif util > 1.0:
                flags.append(f"{c}: {util:.0%} of commit — overage revenue; expansion/re-commit opportunity.")
        for mult in mults:
            units = last_units
            for fm in future:
                units *= 1 + g_used * mult
                scen[mult][fm] += charge(units, commit, up, op)
        base_mult = mults[len(mults) // 2]
        end_units = last_units * (1 + g_used * base_mult) ** a.months
        detail.append((c, seg, int(commit), g, last_rev, charge(end_units, commit, up, op)))

    print(f"### Consumption revenue projection — {future[0]} to {future[-1]}")
    print(f"Last actual month {last_month}: {actual_last:,.0f}\n")
    print("| Scenario | growth x | " + " | ".join(future) + " | Total |")
    print("|---|---|" + "---|" * (len(future) + 1))
    for i, mult in enumerate(mults):
        vals = [scen[mult][m] for m in future]
        print(f"| {names.get(i, f'S{i+1}')} | {mult:.2f} | " + " | ".join(f"{v:,.0f}" for v in vals) + f" | {sum(vals):,.0f} |")
    print("\n#### Customer detail (base)")
    print("| Customer | Segment | Commit units | Trailing growth/mo | Last month rev | Month +" + str(a.months) + " rev |")
    print("|---|---|---|---|---|---|")
    for c, seg, commit, g, lr, er in sorted(detail, key=lambda x: -x[5]):
        print(f"| {c} | {seg} | {commit:,} | {g:+.1%} | {lr:,.0f} | {er:,.0f} |")
    print("\n#### Flags")
    for fl in flags or ["None."]:
        print(f"- {fl}")
    if a.json:
        with open(a.json, "w") as fh:
            json.dump({
                "last_month": last_month, "last_month_revenue": round(actual_last),
                "months": future,
                "scenarios": [{"name": names.get(i, f"S{i+1}"), "multiplier": m,
                               "monthly": [round(scen[m][fm]) for fm in future],
                               "total": round(sum(scen[m][fm] for fm in future))} for i, m in enumerate(mults)],
                "flags": flags,
            }, fh, indent=2)


if __name__ == "__main__":
    main()
