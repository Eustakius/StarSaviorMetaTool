#!/usr/bin/env python3
"""
Star Savior Meta Tool — Meta Scorer
Calculates meta score for a team based on tier weights.
Usage:
  python meta_scorer.py "Lacy" "Emilly" "Hilde" "Luna"
"""

import json
import sys
import os

if getattr(sys, 'frozen', False):
    DATA_PATH = os.path.join(os.path.dirname(sys.executable), "..", "data.json")
else:
    DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data.json")

TIER_WEIGHT = {
    "T0": 5,
    "SS": 4,
    "S": 3,
    "A": 2,
    "B": 1
}


def load_data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def score_team(names, all_characters):
    """Score a team based on tier weights."""
    breakdown = []
    total = 0
    not_found = []

    for name in names:
        match = next((c for c in all_characters if c["name"].lower() == name.lower()), None)
        if match:
            w = TIER_WEIGHT.get(match.get("tier", "B"), 1)
            total += w
            breakdown.append({
                "name": match["name"],
                "tier": match["tier"],
                "role": match["role"],
                "weight": w
            })
        else:
            not_found.append(name)

    # Rating
    max_score = len(names) * 5
    if max_score > 0:
        pct = (total / max_score) * 100
    else:
        pct = 0

    if pct >= 90:
        rating = "SSS — God Tier Team"
    elif pct >= 75:
        rating = "SS — Excellent Team"
    elif pct >= 60:
        rating = "S — Strong Team"
    elif pct >= 40:
        rating = "A — Good Team"
    else:
        rating = "B — Needs Improvement"

    # Role coverage
    roles = [b["role"] for b in breakdown]
    has_support = any(r.lower() == "support" for r in roles)
    has_defender = any(r.lower() == "defender" for r in roles)
    has_dealer = any(r.lower() in ("dealer", "assassin", "caster") for r in roles)

    warnings = []
    if not has_support:
        warnings.append("⚠ No Support — team lacks healing/buffs")
    if not has_defender:
        warnings.append("⚠ No Defender — team lacks survivability")
    if not has_dealer:
        warnings.append("⚠ No Dealer — team lacks damage output")

    return {
        "total_score": total,
        "max_score": max_score,
        "percentage": round(pct, 1),
        "rating": rating,
        "breakdown": breakdown,
        "role_coverage": {
            "support": has_support,
            "defender": has_defender,
            "damage_dealer": has_dealer
        },
        "warnings": warnings,
        "not_found": not_found
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: meta_scorer.py <char1> [char2] [char3] [char4]"}))
        sys.exit(1)

    names = sys.argv[1:]
    data = load_data()
    all_characters = data.get("characters", [])

    result = score_team(names, all_characters)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
