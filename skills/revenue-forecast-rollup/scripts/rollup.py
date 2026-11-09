#!/usr/bin/env python3
"""Roll up bookings / billings / revenue: plan vs forecast vs actual.

Input CSV columns: month (YYYY-MM), segment, product, metric, plan, forecast, actual (blank if open).
Usage:
  python3 rollup.py DATA.csv --period 2026-Q3 [--by segment|product|segment,product] [--json out.json]
Period may be a month (2026-09), a quarter (2026-Q3), or a year (2026).
Amounts are in the file's units (sample data: $K). Prints a markdown table.
"""
import argparse
import csv
import json
import sys
from collections import defaultdict


def months_in(period):
    if "-Q" in period:
        y, q = period.split("-Q")
        q = int(q)
        return [f"{y}-{m:02d}" for m in range(3 * q - 2, 3 * q + 1)]
    if len(period) == 4:
        return [f"{period}-{m:02d}" for m in range(1, 13)]
    return [period]


def num(v):
    return float(v) if v not in ("", None) else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--period", required=True)
    ap.add_argument("--by", default="segment")
    ap.add_argument("--json")
    a = ap.parse_args()

    keys = [k.strip() for k in a.by.split(",") if k.strip()]
    months = set(months_in(a.period))
    agg = defaultdict(lambda: {"plan": 0.0, "forecast": 0.0, "actual": 0.0, "open_forecast": 0.0, "closed_months": set(), "months": set()})
    with open(a.data, newline="") as f:
        rows = list(csv.DictReader(f))
    missing = {"month", "metric", "plan", "forecast", "actual", *keys} - set(rows[0].keys()) if rows else set()
    if missing:
        sys.exit(f"missing columns: {sorted(missing)}")

    for r in rows:
        if r["month"] not in months:
            continue
        k = (r["metric"],) + tuple(r[c] for c in keys)
        g = agg[k]
        g["plan"] += num(r["plan"]) or 0
        g["forecast"] += num(r["forecast"]) or 0
        g["months"].add(r["month"])
        act = num(r["actual"])
        if act is not None:
            g["actual"] += act
            g["closed_months"].add(r["month"])
        else:
            g["open_forecast"] += num(r["forecast"]) or 0

    if not agg:
        sys.exit(f"no rows for period {a.period}")

    out = []
    for k in sorted(agg, key=lambda k: (["bookings", "billings", "revenue"].index(k[0]) if k[0] in ("bookings", "billings", "revenue") else 9, k[1:])):
        g = agg[k]
        closed, total = len(g["closed_months"]), len(g["months"])
        # Latest view: actuals for closed months + current forecast for open months.
        latest = g["actual"] + g["open_forecast"]
        basis = "actual" if closed == total else "forecast" if closed == 0 else f"{closed} act + {total - closed} fcst"
        rec = {"metric": k[0], **{c: v for c, v in zip(keys, k[1:])},
               "plan": round(g["plan"], 1), "forecast": round(g["forecast"], 1),
               "actual": round(g["actual"], 1) if closed else None,
               "latest": round(latest, 1) if latest is not None else None, "basis": basis,
               "closed_months": closed, "total_months": total}
        if latest is not None and g["plan"]:
            rec["var_vs_plan"] = round(latest - g["plan"], 1)
            rec["var_vs_plan_pct"] = round((latest / g["plan"] - 1) * 100, 1)
        out.append(rec)

    # totals per metric
    totals = defaultdict(lambda: {"plan": 0.0, "latest": 0.0, "ok": True})
    for r in out:
        t = totals[r["metric"]]
        t["plan"] += r["plan"]
        if r["latest"] is None:
            t["ok"] = False
        else:
            t["latest"] += r["latest"]

    hdr = ["Metric", *[c.title() for c in keys], "Plan", "Latest", "Basis", "Var $", "Var %"]
    print(f"### Roll-up for {a.period} (by {', '.join(keys)})\n")
    print("| " + " | ".join(hdr) + " |")
    print("|" + "---|" * len(hdr))
    for r in out:
        cells = [r["metric"], *[r[c] for c in keys], f"{r['plan']:,.1f}",
                 "" if r["latest"] is None else f"{r['latest']:,.1f}", r["basis"],
                 "" if "var_vs_plan" not in r else f"{r['var_vs_plan']:+,.1f}",
                 "" if "var_vs_plan_pct" not in r else f"{r['var_vs_plan_pct']:+.1f}%"]
        print("| " + " | ".join(str(c) for c in cells) + " |")
    print()
    for m, t in totals.items():
        if t["ok"] and t["plan"]:
            print(f"- **Total {m}:** latest {t['latest']:,.1f} vs plan {t['plan']:,.1f} "
                  f"({t['latest'] - t['plan']:+,.1f}, {(t['latest'] / t['plan'] - 1) * 100:+.1f}%)")
        else:
            print(f"- **Total {m}:** no plan for period.")

    if a.json:
        with open(a.json, "w") as f:
            json.dump({"period": a.period, "by": keys, "rows": out}, f, indent=2)


if __name__ == "__main__":
    main()
