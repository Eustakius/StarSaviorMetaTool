#!/usr/bin/env python3
"""
Star Savior Meta Tool — Data Engine
Loads and filters character data from data.json.
Usage:
  python data_engine.py                          # returns all characters
  python data_engine.py --tier T0                # filter by tier
  python data_engine.py --role Support           # filter by role
  python data_engine.py --element Fire           # filter by element
  python data_engine.py --name "Lacy"            # search by name
  python data_engine.py --tier T0 --role Dealer  # combine filters
"""

import json
import sys
import os
import argparse

if getattr(sys, 'frozen', False):
    DATA_PATH = os.path.join(os.path.dirname(sys.executable), "..", "data.json")
else:
    DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data.json")


def load_data(path=None):
    """Load character data from data.json."""
    p = path or DATA_PATH
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        return {"error": f"Data file not found: {p}"}
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {str(e)}"}


def filter_characters(characters, tier=None, role=None, element=None, name=None):
    """Filter characters by tier, role, element, or name."""
    results = characters

    if tier:
        results = [c for c in results if c.get("tier", "").upper() == tier.upper()]
    if role:
        results = [c for c in results if c.get("role", "").lower() == role.lower()]
    if element:
        results = [c for c in results if c.get("element", "").lower() == element.lower()]
    if name:
        results = [c for c in results if name.lower() in c.get("name", "").lower()]

    return results


def group_by_tier(characters):
    """Group characters by tier in order: T0, SS, S, A, B."""
    tier_order = ["T0", "SS", "S", "A", "B"]
    grouped = {t: [] for t in tier_order}

    for char in characters:
        t = char.get("tier", "B")
        if t in grouped:
            grouped[t].append(char)

    return grouped


def main():
    parser = argparse.ArgumentParser(description="Star Savior Data Engine")
    parser.add_argument("--tier", type=str, help="Filter by tier (T0, SS, S, A, B)")
    parser.add_argument("--role", type=str, help="Filter by role")
    parser.add_argument("--element", type=str, help="Filter by element")
    parser.add_argument("--name", type=str, help="Search by name")
    parser.add_argument("--grouped", action="store_true", help="Group results by tier")
    parser.add_argument("--data-path", type=str, help="Custom data.json path")

    args = parser.parse_args()

    data = load_data(args.data_path)
    if "error" in data:
        print(json.dumps(data))
        sys.exit(1)

    characters = data.get("characters", [])
    filtered = filter_characters(characters, args.tier, args.role, args.element, args.name)

    if args.grouped:
        result = group_by_tier(filtered)
    else:
        result = filtered

    print(json.dumps({"meta_version": data.get("meta_version", "unknown"), "count": len(filtered), "results": result}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
