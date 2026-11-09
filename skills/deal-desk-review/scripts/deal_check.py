#!/usr/bin/env python3
"""Check deals against deal-desk guardrails and route approvals.

Usage:
  python3 deal_check.py DEALS.csv [--guardrails ../references/guardrails.json] [--deal D-1042]
Deal CSV columns: deal_id, customer, segment, close_date, list_acv, net_acv, term_months,
  payment_terms_days, billing_frequency, ramp (Y/N), usage_commit_units, overage_price, non_standard_terms
Guardrails JSON: see references/guardrails.json (edit to match your approval matrix).
"""
import argparse
import csv
import json
from pathlib import Path

ORDER = ["Deal Desk", "VP Sales", "CRO", "CFO", "Revenue Accounting", "Legal"]


def main():
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser()
    ap.add_argument("deals")
    ap.add_argument("--guardrails", default=str(here.parent / "references" / "guardrails.json"))
    ap.add_argument("--deal")
    ap.add_argument("--json")
    a = ap.parse_args()
    g = json.load(open(a.guardrails))

    with open(a.deals, newline="") as fh:
        deals = [d for d in csv.DictReader(fh) if not a.deal or d["deal_id"] == a.deal]

    print("### Deal-desk guardrail review\n")
    print("| Deal | Customer | Net ACV | Discount | TCV | Approvals | Issues |")
    print("|---|---|---|---|---|---|---|")
    notes = []
    results = []
    for d in deals:
        issues, approvers = [], {"Deal Desk"}
        list_acv, net_acv = float(d["list_acv"]), float(d["net_acv"])
        term = int(d["term_months"])
        disc = round(1 - net_acv / list_acv, 4) if list_acv else 0
        tcv = net_acv * term / 12
        for tier in g["discount_tiers"]:
            if disc > tier["above_pct"] / 100:
                approvers.add(tier["approver"])
        if disc > g["discount_tiers"][-1]["above_pct"] / 100:
            issues.append(f"discount {disc:.0%} beyond top tier")
        pt = int(d["payment_terms_days"])
        if pt > g["payment_terms"]["standard_max_days"]:
            approvers.add(g["payment_terms"]["approver"])
            issues.append(f"net {pt} payment terms")
        if term > g["term"]["standard_max_months"]:
            approvers.add(g["term"]["approver"])
            issues.append(f"{term}-month term")
        if d["billing_frequency"] not in g["billing"]["standard"]:
            approvers.add(g["billing"]["approver"])
            issues.append(f"{d['billing_frequency']} billing (cash timing)")
        if d["ramp"].upper() == "Y":
            approvers.update(g["ramp"]["approvers"])
            issues.append("ramped pricing (ASC 606: allocate transaction price; check material right)")
        if d.get("overage_price"):
            op = float(d["overage_price"])
            floor = g["usage"]["min_overage_price"]
            if op < floor:
                approvers.add(g["usage"]["approver"])
                issues.append(f"overage price {op} below floor {floor}")
            if float(d.get("usage_commit_units") or 0) > 0:
                issues.append("usage commit (forecast breakage; variable consideration)")
        nst = (d.get("non_standard_terms") or "").lower()
        for term_kw, rule in g["non_standard_terms"].items():
            if term_kw in nst:
                approvers.update(rule["approvers"])
                issues.append(f"{term_kw}: {rule['why']}")
        if tcv >= g["large_deal_tcv"]["threshold"]:
            approvers.add(g["large_deal_tcv"]["approver"])
        ordered = [x for x in ORDER if x in approvers] + sorted(approvers - set(ORDER))
        print(f"| {d['deal_id']} | {d['customer']} | {net_acv:,.0f} | {disc:.0%} | {tcv:,.0f} | {', '.join(ordered)} | {'; '.join(issues) or 'within guardrails'} |")
        results.append({"deal_id": d["deal_id"], "customer": d["customer"], "segment": d["segment"], "close_date": d["close_date"],
                        "net_acv": net_acv, "discount_pct": round(disc * 100, 1), "tcv": round(tcv), "approvers": ordered, "issues": issues})
        if d["close_date"][5:7] in ("03", "06", "09", "12") and len(ordered) >= 4:
            notes.append(f"{d['deal_id']}: {len(ordered)} approvers and a quarter-end close date — start approvals now or risk slip.")
    if a.json:
        with open(a.json, "w") as fh:
            json.dump({"deals": results, "timing_risk": notes}, fh, indent=2)
    if notes:
        print("\n#### Timing risk")
        for n in notes:
            print(f"- {n}")


if __name__ == "__main__":
    main()
