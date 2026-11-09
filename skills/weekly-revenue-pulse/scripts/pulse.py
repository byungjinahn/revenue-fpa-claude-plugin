#!/usr/bin/env python3
"""Run the four revenue-fpa checks on one data folder and combine them into pulse.json.

Usage:
  python3 pulse.py --data DIR --as-of 2026-11-09 --out DIR/pulse.json
DIR must hold revenue_plan_forecast_actuals.csv, usage_history.csv, deals.csv.
Calls the sibling skills' scripts, so every number in pulse.json comes from them.
"""
import argparse
import datetime as dt
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SKILLS = Path(__file__).resolve().parents[2]


def usd(k):
    """Revenue file is in $K; dashboard files are in whole dollars."""
    return None if k is None else round(k * 1000)


def run(script, *args):
    p = subprocess.run([sys.executable, str(SKILLS / script), *map(str, args)], capture_output=True, text=True)
    if p.returncode:
        sys.exit(f"{script} failed:\n{p.stderr}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--as-of", default=dt.date.today().isoformat())
    ap.add_argument("--out", required=True)
    ap.add_argument("--datasets-dir", help="also write one JSON row file per dashboard card here")
    a = ap.parse_args()
    d = Path(a.data)
    as_of = dt.date.fromisoformat(a.as_of)
    quarter = f"{as_of.year}-Q{(as_of.month - 1) // 3 + 1}"
    first = as_of.replace(day=1)
    last_closed = (first - dt.timedelta(days=1)).strftime("%Y-%m")
    t = Path(tempfile.mkdtemp())

    run("revenue-forecast-rollup/scripts/rollup.py", d / "revenue_plan_forecast_actuals.csv", "--period", quarter, "--by", "segment", "--json", t / "r.json")
    run("forecast-variance/scripts/variance.py", d / "revenue_plan_forecast_actuals.csv", "--month", last_closed, "--json", t / "v.json")
    run("consumption-revenue-model/scripts/consumption_model.py", d / "usage_history.csv", "--months", 3, "--json", t / "c.json")
    run("deal-desk-review/scripts/deal_check.py", d / "deals.csv", "--json", t / "d.json")
    r, v, c, dd = (json.load(open(t / f)) for f in ("r.json", "v.json", "c.json", "d.json"))

    totals = {}
    for row in r["rows"]:
        m = totals.setdefault(row["metric"], {"plan": 0.0, "latest": 0.0})
        m["plan"] += row["plan"]
        m["latest"] += row["latest"]
    for m in totals.values():
        m["plan"], m["latest"] = round(m["plan"], 1), round(m["latest"], 1)
        m["var"] = round(m["latest"] - m["plan"], 1)
        m["var_pct"] = round((m["latest"] / m["plan"] - 1) * 100, 1) if m["plan"] else None

    deals = dd["deals"]
    pulse = {
        "as_of": as_of.isoformat(),
        "week": "%d-W%02d" % as_of.isocalendar()[:2],
        "quarter": quarter,
        "units": {"revenue_file": "$K", "usage": "$"},
        "quarter_totals": totals,
        "quarter_by_segment": r["rows"],
        "variance": v,
        "consumption": c,
        "deals": {
            "count": len(deals),
            "net_acv": round(sum(x["net_acv"] for x in deals)),
            "within_guardrails": sum(1 for x in deals if not x["issues"]),
            "needs_cfo": sum(1 for x in deals if "CFO" in x["approvers"]),
            "list": deals,
            "timing_risk": dd["timing_risk"],
        },
        "commentary": None,
    }
    Path(a.out).write_text(json.dumps(pulse, indent=2))

    if a.datasets_dir:
        ds = Path(a.datasets_dir)
        ds.mkdir(parents=True, exist_ok=True)
        anom = {(x["segment"], x["product"], x["metric"]): x["z"] for x in v["anomalies"]}
        tables = {
            "pulse_info": [{
                "as_of": pulse["as_of"], "week": pulse["week"], "quarter": quarter, "last_closed_month": last_closed,
                "deals_count": pulse["deals"]["count"], "deals_within": pulse["deals"]["within_guardrails"],
                "deals_need_cfo": pulse["deals"]["needs_cfo"], "deals_net_acv": pulse["deals"]["net_acv"],
                "material_count": len(v["material"]), "anomaly_count": len(v["anomalies"]),
            }],
            "quarter_totals": [{"metric": k, "plan": usd(m["plan"]), "latest": usd(m["latest"]), "var": usd(m["var"]), "var_pct": m["var_pct"]}
                               for k, m in totals.items()],
            "quarter_segments": [{"metric": x["metric"], "segment": x["segment"], "plan": usd(x["plan"]), "latest": usd(x["latest"]),
                                  "var": usd(x.get("var_vs_plan")), "var_pct": x.get("var_vs_plan_pct"), "basis": x["basis"]}
                                 for x in r["rows"]],
            "variance": [{**x, **{f: usd(x[f]) for f in ("plan", "forecast", "actual", "var")},
                          "anomaly_z": anom.get((x["segment"], x["product"], x["metric"]))} for x in v["material"]][:8],
            "usage_scenarios": [{"scenario": s["name"], "month": m, "revenue": val}
                                for s in c["scenarios"] for m, val in zip(c["months"], s["monthly"])],
            "usage_flags": [{"customer": f.split(":")[0], "flag": f.split(": ", 1)[1],
                             "type": "risk" if "shortfall" in f else "expansion" if "overage" in f else "check"} for f in c["flags"]],
            "deals": [{"deal_id": x["deal_id"], "customer": x["customer"], "close_date": x["close_date"], "net_acv": x["net_acv"],
                       "discount_pct": x["discount_pct"], "approvers": len(x["approvers"]),
                       "issues": "; ".join(i.split(" (")[0] for i in x["issues"]) or "Within guardrails"}
                      for x in sorted(deals, key=lambda x: -len(x["approvers"]))],
        }
        for name, rows in tables.items():
            (ds / f"{name}.json").write_text(json.dumps(rows, indent=1))
        print(f"wrote {len(tables)} dataset files to {ds}")
    print(f"wrote {a.out}: {quarter} latest revenue {totals['revenue']['latest']:,.1f} vs plan {totals['revenue']['plan']:,.1f}; "
          f"{len(v['material'])} material variances in {last_closed}; {len(deals)} deals")


if __name__ == "__main__":
    main()
