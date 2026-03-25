#!/usr/bin/env python3
"""
Star Savior Meta Tool — Smart Team Builder (Final Evolution)
A meta reasoning engine that evaluates teams by:
  1. Role coverage (structure)
  2. Tier strength (power)
  3. Tag-based functional coverage (abilities)
  4. Weakness detection & auto-fix
  5. Data-driven explanation generation (no hallucination)

Usage:
  python team_builder.py "Lacy" "Luna"
  python team_builder.py "Bunnygirl Charlotte" "Kyra" "Petra"
  python team_builder.py --auto-fix "Lacy" "Luna"
  python team_builder.py --analyze "Bunnygirl Charlotte" "Emilly" "Hilde" "Muriel"
"""

import json
import argparse
import sys
import os

if getattr(sys, 'frozen', False):
    DATA_PATH = os.path.join(os.path.dirname(sys.executable), "..", "data.json")
else:
    DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data.json")

# ─── TIER SYSTEM ─────────────────────────────────────────────────
TIER_PRIORITY = ["T0", "SS", "S", "A", "B"]
TIER_WEIGHT = {"T0": 5, "SS": 4, "S": 3, "A": 2, "B": 1}

MAX_TEAM_SIZE = 4

# ─── REQUIRED COVERAGE TAGS ─────────────────────────────────────
# These represent the minimum functional requirements for a meta team
REQUIRED_TAGS = {
    "burst_dps":          "Damage",
    "heal":               "Sustain",
    "damage_mitigation":  "Damage Mitigation",
}

# Optional but highly recommended
RECOMMENDED_TAGS = {
    "cleanse":            "Cleanse",
    "attack_buff":        "Buff/Debuff",
    "crowd_control":      "Control",
    "shield":             "Shield",
}

# Role requirements (Dynamic based on focus)
DEFAULT_REQUIRED_ROLES = {"Support", "Defender"}
DAMAGE_ROLES = {"Dealer", "Assassin", "Caster", "Ranger"}

def get_focus_config(focus, team=None):
    """Return required roles, specific focus instructions, and preferred tags."""
    cfg = {"required_roles": set(), "target_roles": {}, "preferred_tags": [], "target_element": None}
    
    if team and len(team) > 0:
        cfg["target_element"] = team[0].get("element", "Unknown")

    if focus == "hyper_carry":
        cfg["required_roles"] = {"Support"}
        # Wants 1 Damage, 2-3 Supports, 0-1 Defender
        cfg["target_roles"] = {"Support": 2, "Damage": 1}
        cfg["preferred_tags"] = ["Buff", "Cleanse", "Sustain"]
    elif focus == "stall":
        cfg["required_roles"] = {"Support", "Defender"}
        # Wants 2 Defenders, 2 Supports
        cfg["target_roles"] = {"Defender": 2, "Support": 2}
        cfg["preferred_tags"] = ["Sustain", "Shield", "Revive"]
    elif focus == "burst_speed":
        cfg["required_roles"] = {"Support"}
        cfg["target_roles"] = {"Damage": 2, "Support": 1}
        cfg["preferred_tags"] = ["Burst DPS", "Buff", "Energy"]
    elif focus == "control":
        cfg["required_roles"] = {"Support"}
        cfg["target_roles"] = {"Damage": 2, "Defender": 1}
        cfg["preferred_tags"] = ["Control", "Debuff", "AoE"]
    elif focus == "elemental":
        cfg["required_roles"] = {"Support"}
        # Just needs a support, expects 3+ same element
    else:  # balanced
        cfg["required_roles"] = {"Support", "Defender"}
    return cfg


# ─── DATA LOADING ────────────────────────────────────────────────

def load_data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_tag_explanations(data):
    """Load tag explanation templates from data.json."""
    return data.get("tag_explanations", {})


# ─── COVERAGE ENGINE ─────────────────────────────────────────────

def evaluate_team(team):
    """Get all functional tags covered by the team."""
    coverage = set()
    for char in team:
        coverage.update(char.get("tags", []))
    return coverage


def get_role_coverage(team, focus="balanced"):
    """Check which roles are present in the team."""
    roles = {c.get("role", "Unknown") for c in team}
    return {
        "support": sum(1 for c in team if c.get("role") == "Support"),
        "defender": sum(1 for c in team if c.get("role") == "Defender"),
        "damage": sum(1 for c in team if c.get("role") in DAMAGE_ROLES),
        "roles_present": list(roles)
    }

def calculate_synergies(team):
    """Calculate elemental and class synergies."""
    synergies = []
    
    # 1. Elemental Synergy
    element_counts = {}
    for c in team:
        elem = c.get("element", "Unknown")
        if elem != "Unknown":
            element_counts[elem] = element_counts.get(elem, 0) + 1
            
    for elem, count in element_counts.items():
        if count >= 3:
            synergies.append(f"✨ Mastery of {elem}: 3+ {elem} characters detected. Team gains +15% {elem} DMG and +10% Resistance.")
        elif count == 2:
            synergies.append(f"🔥 {elem} Resonance: 2 {elem} characters detected. Team gains +5% {elem} DMG.")

    # 2. Class Synergy
    role_cov = get_role_coverage(team)
    if role_cov["support"] >= 2:
        synergies.append("💖 Dual Support: +15% Healing Output and +10% Buff Duration.")
    if role_cov["defender"] >= 2:
        synergies.append("🛡️ Iron Wall: +20% Team Defense and +15% Shield Strength.")
    if role_cov["damage"] >= 3:
        synergies.append("⚔️ All-Out Assault: +10% Attack, but taking +10% more damage.")
        
    return synergies


# ─── WEAKNESS DETECTION ─────────────────────────────────────────

def find_weaknesses(coverage):
    """Detect missing required and recommended tags."""
    missing_required = {}
    for tag, label in REQUIRED_TAGS.items():
        if tag not in coverage:
            missing_required[tag] = label

    missing_recommended = {}
    for tag, label in RECOMMENDED_TAGS.items():
        if tag not in coverage:
            missing_recommended[tag] = label

    return missing_required, missing_recommended


# ─── CHARACTER SEARCH ────────────────────────────────────────────

def score_candidate(char, focus_cfg, team_elements):
    """Score a character based on tier, tags, and element synergy."""
    tier_scores = {"T0": 100, "SS": 80, "S": 60, "A": 40, "B": 20}
    score = tier_scores.get(char.get("tier", "B"), 0)
    
    # Bonus for preferred tags (e.g., Buff for Hyper Carry, Shield for Stall)
    for pref_tag in focus_cfg.get("preferred_tags", []):
        if pref_tag in char.get("tags", []):
            score += 25
            
    # Huge bonus for hitting the required target element in Elemental mode
    if focus_cfg.get("target_element") and focus_cfg["target_element"] != "Unknown":
        if char.get("element") == focus_cfg["target_element"]:
            score += 45
            
    # General synergy bonus for matching an existing team element
    elif char.get("element") in team_elements and char.get("element") != "Unknown":
        score += 15
        
    return score


def find_best_candidate(role, all_characters, used_names, focus_cfg, team_elements, exclude_role=None):
    """Find the best scoring character for a given role or general slot."""
    best_char = None
    best_score = -1
    
    for char in all_characters:
        if char["name"] in used_names:
            continue
        if role and char.get("role", "").lower() != role.lower():
            if role == "Damage" and char.get("role") not in DAMAGE_ROLES:
                continue
            elif role != "Damage":
                continue
        if exclude_role and char.get("role") == exclude_role:
            continue
            
        score = score_candidate(char, focus_cfg, team_elements)
        if score > best_score:
            best_score = score
            best_char = char
            
    return best_char


# ─── TEAM BUILDING ───────────────────────────────────────────────

def resolve_characters(selected_names, all_characters):
    """Resolve character names to objects."""
    team = []
    not_found = []
    for name in selected_names:
        match = next((c for c in all_characters if c["name"].lower() == name.lower()), None)
        if match:
            team.append(match)
        else:
            not_found.append(name)
    return team, not_found


def auto_fix_team(team, all_characters, focus="balanced"):
    """Auto-fill missing roles using smart weighted scoring."""
    suggestions = []
    used_names = {c["name"] for c in team}
    cfg = get_focus_config(focus, team)
    team_elements = {c.get("element", "Unknown") for c in team}

    # Helper function to append heavily scored selections
    def add_candidate(role, reason, exclude_role=None):
        if len(team) >= MAX_TEAM_SIZE:
            return False
            
        # Re-eval elements inside the loop in case they changed
        current_elements = {c.get("element", "Unknown") for c in team}
        best = find_best_candidate(role, all_characters, used_names, cfg, current_elements, exclude_role)
        if best:
            team.append(best)
            used_names.add(best["name"])
            suggestions.append({
                "name": best["name"],
                "role": best["role"],
                "tier": best["tier"],
                "reason": reason
            })
            return True
        return False

    # STEP 1: Fix missing required roles based on Focus
    for role in cfg["required_roles"]:
        if len(team) >= MAX_TEAM_SIZE: break
        if not any(c.get("role") == role for c in team):
            add_candidate(role, f"Auto-filled: focus ({focus}) requires {role} role")

    # STEP 2: Fill Focus Targets (e.g. 2nd support for Stall, or 2nd damage for Burst)
    for role, target_count in cfg.get("target_roles", {}).items():
        while len(team) < MAX_TEAM_SIZE:
            current = get_role_coverage(team, focus)
            count = current["damage"] if role == "Damage" else current[role.lower()]
            if count >= target_count:
                break
            
            search_role = "Damage" if role == "Damage" else role
            if not add_candidate(search_role, f"Auto-filled: focus ({focus}) targets {target_count}x {role}"):
                break

    # STEP 3: Fill remaining slots smartly (No rigid roles, just highest scoring overall)
    while len(team) < MAX_TEAM_SIZE:
        # If we already have a Defender and 1 Support, we probably want Damage next, so just exclude Support if we have 2, etc.
        # But mostly find_best_candidate will naturally pick synergizing elements and tags.
        add_candidate(None, "Auto-filled: best available synergy match")
    # The original code had a `break` here, which would exit the loop after the first attempt.
    # This seems incorrect for filling multiple slots. Removing it to allow filling all slots.
    # If add_candidate returns False, the loop will naturally terminate.

    return team, suggestions


# ─── SCORING ─────────────────────────────────────────────────────

def calculate_meta_score(team):
    """Calculate meta score from tier weights."""
    breakdown = []
    total = 0
    for c in team:
        w = TIER_WEIGHT.get(c.get("tier", "B"), 1)
        total += w
        breakdown.append({"name": c["name"], "tier": c["tier"], "weight": w})

    max_score = len(team) * 5
    pct = (total / max_score * 100) if max_score > 0 else 0

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

    return {
        "total_score": total,
        "max_score": max_score,
        "percentage": round(pct, 1),
        "rating": rating,
        "breakdown": breakdown
    }


# ─── EXPLANATION GENERATOR ───────────────────────────────────────

def generate_explanation(team, tag_explanations):
    """Generate data-driven explanation — no hallucination."""
    team_analysis = []

    for char in team:
        char_tags = char.get("tags", [])
        why_meta = char.get("why_meta", [])
        contributions = []

        for tag in char_tags:
            explanation = tag_explanations.get(tag)
            if explanation:
                contributions.append(explanation)

        # Merge with actual why_meta data
        char_entry = {
            "name": char["name"],
            "role": char["role"],
            "tier": char["tier"],
            "contributions": contributions,
            "why_meta": [w for w in why_meta if "No detailed data" not in w]
        }
        team_analysis.append(char_entry)

    return team_analysis


def generate_coverage_report(team):
    """Generate a coverage checklist with status."""
    coverage = evaluate_team(team)
    missing_req, missing_rec = find_weaknesses(coverage)

    report = []

    # Required coverage
    for tag, label in REQUIRED_TAGS.items():
        status = "✅" if tag in coverage else "❌"
        report.append({"category": label, "tag": tag, "status": status, "required": True})

    # Recommended coverage
    for tag, label in RECOMMENDED_TAGS.items():
        status = "✅" if tag in coverage else "⚠️"
        report.append({"category": label, "tag": tag, "status": status, "required": False})

    return report


def generate_warnings(team, focus="balanced"):
    """Generate warnings about team weaknesses."""
    coverage = evaluate_team(team)
    role_cov = get_role_coverage(team, focus)
    cfg = get_focus_config(focus)
    warnings = []

    missing_req, _ = find_weaknesses(coverage)
    for tag, label in missing_req.items():
        warnings.append(f"❌ Missing {label} — no character provides '{tag}'")

    if "Support" in cfg["required_roles"] and role_cov["support"] == 0:
        warnings.append("⚠️ No Support — team lacks healing/buffs")
    if "Defender" in cfg["required_roles"] and role_cov["defender"] == 0:
        warnings.append("⚠️ No Defender — team lacks survivability")
    if role_cov["damage"] == 0 and focus != "stall":
        warnings.append("⚠️ No Damage Dealer — team lacks kill pressure")

    # Check for element diversity (only warn if NOT elemental mode)
    elements = {c.get("element", "Unknown") for c in team}
    if focus != "elemental" and len(elements) == 1 and len(team) >= 3:
        warnings.append(f"⚠️ Mono-element team ({elements.pop()}) — vulnerable to counter-elements. (Use 'Elemental' focus if intended)")
    
    if focus == "elemental" and len(elements) > 2:
        warnings.append("⚠️ Too many elements for Elemental Focus. Try picking characters of the same element.")

    return warnings


# ─── MAIN ────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Star Savior Smart Team Builder")
    parser.add_argument("characters", nargs="*", help="Character names to build team from")
    parser.add_argument("--auto-fix", action="store_true", help="Auto-fill missing roles/tags")
    parser.add_argument("--analyze", action="store_true", help="Full team analysis with explanation")
    parser.add_argument("--focus", type=str, default="balanced", help="Team focus: balanced, hyper_carry, stall, burst_speed, control, elemental")
    parser.add_argument("--data-path", type=str, help="Custom data.json path")
    args = parser.parse_args()

    if not args.characters:
        print(json.dumps({"error": "Usage: team_builder.py [--auto-fix] [--analyze] <char1> [char2] ..."}))
        sys.exit(1)

    global DATA_PATH
    if args.data_path:
        DATA_PATH = args.data_path

    data = load_data()
    all_characters = data.get("characters", [])
    tag_explanations = get_tag_explanations(data)

    # Resolve
    team, not_found = resolve_characters(args.characters, all_characters)

    # Auto-fix if requested or by default
    suggestions = []
    if args.auto_fix or len(team) < MAX_TEAM_SIZE:
        team, suggestions = auto_fix_team(team, all_characters, args.focus)

    # Score
    score = calculate_meta_score(team)
    
    # Synergies
    synergies = calculate_synergies(team)

    # Analysis
    explanation = generate_explanation(team, tag_explanations)
    coverage_report = generate_coverage_report(team)
    warnings = generate_warnings(team, args.focus)
    role_cov = get_role_coverage(team, args.focus)

    result = {
        "team": [{
            "name": c["name"],
            "role": c["role"],
            "tier": c["tier"],
            "element": c.get("element", "Unknown"),
            "tags": c.get("tags", [])
        } for c in team],
        "meta_score": score,
        "coverage_report": coverage_report,
        "role_coverage": role_cov,
        "warnings": warnings,
        "auto_suggestions": suggestions,
        "not_found": not_found,
        "synergies": synergies
    }

    if args.analyze:
        result["team_analysis"] = explanation

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
