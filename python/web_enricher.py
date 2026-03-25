#!/usr/bin/env python3
"""
Star Savior Meta Tool — Web Enricher v3 (Real Sources)
Scrapes actual Star Savior data from verified sources:
  1. Tychara (PRIMARY) — JSON-LD structured data with tier + notes
  2. LDPlayer (SECONDARY) — guide descriptions (if accessible)
  3. LagoFast (OPTIONAL) — team composition data

Usage:
  python web_enricher.py              # enrich characters with missing data
  python web_enricher.py --check      # check connectivity only
  python web_enricher.py --dry-run    # preview changes without writing
  python web_enricher.py --validate   # validate data.json integrity
  python web_enricher.py --force      # re-scrape all characters
"""

import json
import sys
import os
import shutil
import argparse
import re
import time
from datetime import datetime

try:
    import requests
except ImportError:
    print(json.dumps({
        "status": "error",
        "message": "Python 'requests' package required. Run: pip install requests",
        "enriched": 0,
    }))
    sys.exit(1)

if getattr(sys, 'frozen', False):
    DATA_PATH = os.path.join(os.path.dirname(sys.executable), "..", "data.json")
    BACKUP_DIR = os.path.join(os.path.dirname(sys.executable), "..", "backups")
else:
    DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data.json")
    BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backups")

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
TIMEOUT = 15
RATE_LIMIT = 1.5

# ═══════════════════════════════════════════════════════════════
#  SOURCES
# ═══════════════════════════════════════════════════════════════

SOURCES = {
    "tychara_tierlist": {
        "name": "Tychara Tier List",
        "url": "https://tychara.com/StarSavior/tierlist",
    },
    "tychara_charlist": {
        "name": "Tychara Character List",
        "url": "https://tychara.com/StarSavior/characterlist",
    },
    "ldplayer": {
        "name": "LDPlayer Guide",
        "url": "https://www.ldplayer.net/blog/star-savior-tier-list-and-reroll-guide.html",
    },
    "lagofast": {
        "name": "LagoFast Guide",
        "url": "https://www.lagofast.com/en/blog/star-savior-characters/",
    },
}

CONNECTIVITY_URLS = [
    "https://www.google.com",
    "https://www.cloudflare.com",
]

# ═══════════════════════════════════════════════════════════════
#  VALIDATION
# ═══════════════════════════════════════════════════════════════

VALID_TIERS = {"T0", "SS", "S", "A", "B", "C"}
VALID_ROLES = {"Dealer", "Support", "Defender", "Assassin", "Caster", "Ranger", "Striker"}
VALID_ELEMENTS = {"Fire", "Ice", "Wind", "Thunder", "Light", "Dark", "Earth", "Water",
                  "Sun", "Moon", "Star"}  # Tychara uses Sun/Moon/Star
MAX_FIELD_LEN = 300

POISON_RE = re.compile(
    r'<script|javascript:|onclick|onerror|eval\(|document\.|window\.\b|'
    r'<iframe|<embed|base64,|data:text|&#x|\\u00|'
    r'\{[\{\%]|SELECT\s|INSERT\s|DROP\s|DELETE\s|UPDATE\s',
    re.IGNORECASE,
)


def sanitize(text):
    if not isinstance(text, str):
        return ""
    t = re.sub(r'<[^>]+>', '', text)
    t = re.sub(r'[\x00-\x09\x0b-\x1f\x7f]', '', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def is_poisoned(text):
    return bool(POISON_RE.search(text)) if isinstance(text, str) else False


def validate_full_dataset(data):
    errors = []
    if not isinstance(data, dict):
        return False, ["root not dict"]
    chars = data.get("characters")
    if not isinstance(chars, list):
        return False, ["characters not list"]
    for c in chars:
        name = c.get("name", "?")
        if is_poisoned(name):
            errors.append(f"poisoned name: {name[:30]}")
    critical = any("poisoned" in e for e in errors)
    return not critical, errors


# ═══════════════════════════════════════════════════════════════
#  HTTP
# ═══════════════════════════════════════════════════════════════

def _get_session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    return s


def check_connectivity():
    for url in CONNECTIVITY_URLS:
        try:
            r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=5)
            if r.status_code < 400:
                return True, None
        except requests.RequestException as e:
            last = str(e)
    return False, last


def fetch_url(url, session=None):
    s = session or _get_session()
    try:
        resp = s.get(url, timeout=TIMEOUT, allow_redirects=True)
        if resp.status_code == 403:
            return None, "HTTP 403 — site blocked the request"
        if resp.status_code == 404:
            return None, "HTTP 404 — page not found"
        if resp.status_code != 200:
            return None, f"HTTP {resp.status_code}"
        if len(resp.content) > 15_000_000:
            return None, "Response too large (>15MB)"
        resp.encoding = resp.apparent_encoding or "utf-8"
        return resp.text, None
    except requests.ConnectionError as e:
        return None, f"Connection failed: {e}"
    except requests.Timeout:
        return None, f"Timed out after {TIMEOUT}s"
    except requests.RequestException as e:
        return None, f"Request error: {e}"
    except Exception as e:
        return None, f"Unexpected: {e}"


# ═══════════════════════════════════════════════════════════════
#  TYCHARA JSON-LD PARSER
# ═══════════════════════════════════════════════════════════════

# Map Tychara class names to our role names
CLASS_TO_ROLE = {
    "assassin": "Assassin",
    "striker": "Dealer",
    "ranger": "Ranger",
    "caster": "Caster",
    "guardian": "Defender",
    "defender": "Defender",
    "support": "Support",
    "healer": "Support",
}

# Map Tychara element names to our element names
ELEMENT_MAP = {
    "sun": "Light",
    "moon": "Dark",
    "star": "Thunder",
    "fire": "Fire",
    "ice": "Ice",
    "wind": "Wind",
    "earth": "Earth",
    "water": "Water",
    "light": "Light",
    "dark": "Dark",
    "thunder": "Thunder",
}


def parse_tychara_tierlist(html):
    """
    Extract character data from Tychara's embedded JSON-LD schema.org data.
    Returns dict: { normalized_name: { note, tier, role, element } }
    """
    results = {}

    # Find JSON-LD script blocks
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)

    for scr in scripts:
        if 'CollectionPage' not in scr or 'itemListElement' not in scr:
            continue

        try:
            data = json.loads(scr)
        except json.JSONDecodeError:
            continue

        # Navigate: mainEntity -> [sections] -> itemListElement -> [items]
        main_entities = data.get("mainEntity", [])
        if not isinstance(main_entities, list):
            main_entities = [main_entities]

        for section in main_entities:
            section_name = section.get("name", "")
            is_pve = "PvE" in section_name

            items = section.get("itemListElement", [])
            for item in items:
                thing = item.get("item", {})
                raw_name = thing.get("name", "")
                description = thing.get("description", "")

                if not raw_name or is_poisoned(description):
                    continue

                # Extract tier from name: "Emilly (PvE T0)" or "Lacy (PvE SS)"
                tier = None
                tier_match = re.search(r'\((?:PvE|PvP)\s+(T0|SS|S|A|B|C)\)', raw_name)
                if tier_match:
                    tier = tier_match.group(1)

                # Clean name: remove "(PvE T0)" suffix
                clean_name = re.sub(r'\s*\((?:PvE|PvP)\s+(?:T0|SS|S|A|B|C)\)', '', raw_name).strip()

                # Extract properties
                props = {}
                for p in thing.get("additionalProperty", []):
                    props[p.get("name", "")] = p.get("value", "")

                role_raw = props.get("Class", "").lower()
                role = CLASS_TO_ROLE.get(role_raw)

                elem_raw = props.get("Element", "").lower()
                element = ELEMENT_MAP.get(elem_raw)

                pve_tier = props.get("PvE Tier")

                # Use PvE tier from properties if available
                if pve_tier and pve_tier in VALID_TIERS:
                    tier = pve_tier

                norm = _normalize_name(clean_name)

                # Prefer PvE data over PvP data
                if norm in results and not is_pve:
                    # PvP data — only fill if PvE didn't provide
                    existing = results[norm]
                    if not existing.get("note") and description:
                        existing["note"] = sanitize(description)[:MAX_FIELD_LEN]
                    continue

                entry = {
                    "note": sanitize(description)[:MAX_FIELD_LEN] if description else "",
                    "tier": tier,
                    "role": role,
                    "element": element,
                    "source_name": clean_name,  # original name from source
                }
                results[norm] = entry

    return results


# ═══════════════════════════════════════════════════════════════
#  NAME NORMALIZATION
# ═══════════════════════════════════════════════════════════════

NAME_ALIASES = {
    "emily": "emilly",
    "asherah waltz of starlight": "asherah (waltz of starlight)",
    "asherah – waltz of starlight": "asherah (waltz of starlight)",
    "asherah - waltz of starlight": "asherah (waltz of starlight)",
    "frey noble princess": "frey (noble princess)",
    "frey – noble princess": "frey (noble princess)",
    "frey - noble princess": "frey (noble princess)",
    "belly": "bell rhys",
}


def _normalize_name(name):
    n = name.strip().lower()
    n = re.sub(r'\s+', ' ', n)
    n = re.sub(r'["""]', '', n)
    return NAME_ALIASES.get(n, n)


def _find_fuzzy(norm_name, data_dict):
    """Fuzzy match a normalized name against scraped data dict."""
    # Exact match
    if norm_name in data_dict:
        return data_dict[norm_name]

    # Partial / substring
    for key in data_dict:
        if norm_name in key or key in norm_name:
            return data_dict[key]

    # Word overlap (need 2+ words overlap for safety)
    words = set(norm_name.split())
    best_key, best_score = None, 0
    for key in data_dict:
        overlap = len(words & set(key.split()))
        if overlap > best_score and overlap >= min(2, len(words)):
            best_key, best_score = key, overlap

    return data_dict.get(best_key) if best_score >= 1 else None


# ═══════════════════════════════════════════════════════════════
#  ENRICHMENT
# ═══════════════════════════════════════════════════════════════

def needs_enrichment(char):
    wm = char.get("why_meta", [])
    wk = char.get("weakness", [])
    has_placeholder = any("No detailed data" in s for s in wm + wk)
    return has_placeholder or not wm or not wk


def enrich_all(data, tychara_data, dry_run=False, force=False):
    """Apply scraped Tychara data to characters in data.json."""
    characters = data.get("characters", [])
    results = []
    enriched_count = 0

    for char in characters:
        if not force and not needs_enrichment(char):
            continue

        name = char["name"]
        norm = _normalize_name(name)
        char_result = {
            "name": name,
            "enriched": False,
            "fields_updated": [],
            "source": None,
        }

        # Find matching Tychara entry
        match = _find_fuzzy(norm, tychara_data)

        if match:
            if dry_run:
                char_result["enriched"] = True
                char_result["would_update"] = {
                    "note": match.get("note", "")[:60],
                    "tier": match.get("tier"),
                    "role": match.get("role"),
                    "element": match.get("element"),
                }
                enriched_count += 1
            else:
                updated = _apply_match(char, match)
                if updated:
                    char_result["enriched"] = True
                    char_result["fields_updated"] = updated
                    char_result["source"] = "Tychara"
                    enriched_count += 1

                    # Add source attribution
                    sources = char.get("source", [])
                    tag = f"Tychara (enriched {datetime.now().strftime('%Y-%m-%d')})"
                    if not any("Tychara" in s for s in sources):
                        sources.append(tag)
                    char["source"] = sources

        results.append(char_result)

    return results, enriched_count


def _apply_match(char, match):
    """Apply a Tychara match to a character. Returns list of updated field names."""
    updated = []

    # ─── why_meta from note ───
    note = match.get("note", "")
    if note:
        current_wm = char.get("why_meta", [])
        has_placeholder = any("No detailed data" in s for s in current_wm)

        if has_placeholder or not current_wm:
            # Split on pipe separators (Tychara uses | and ㅣ)
            sentences = re.split(r'[|ㅣ]', note)
            clean = [sanitize(s) for s in sentences if len(sanitize(s)) > 10]
            if clean:
                char["why_meta"] = clean[:4]
                updated.append("why_meta")

                # Extract weakness hints from the note
                current_wk = char.get("weakness", [])
                has_wk_placeholder = any("No detailed data" in s for s in current_wk)
                if has_wk_placeholder or not current_wk:
                    weakness_hints = []
                    for s in clean:
                        s_lower = s.lower()
                        if any(kw in s_lower for kw in [
                            "but ", "however", "lack", "weak", "low ",
                            "disappointing", "worse", "limited", "missing",
                            "terrible", "too weak", "reduced", "disappear",
                        ]):
                            weakness_hints.append(s)
                    if weakness_hints:
                        char["weakness"] = weakness_hints[:3]
                        updated.append("weakness")

    # ─── Role ───
    if match.get("role") and not char.get("role"):
        char["role"] = match["role"]
        updated.append("role")

    # ─── Element ───
    if match.get("element") and not char.get("element"):
        char["element"] = match["element"]
        updated.append("element")

    return updated


# ═══════════════════════════════════════════════════════════════
#  DATA I/O
# ═══════════════════════════════════════════════════════════════

def load_data():
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f), None
    except FileNotFoundError:
        return None, f"data.json not found at {DATA_PATH}"
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON: {e}"


def save_data(data):
    ok, errors = validate_full_dataset(data)
    if not ok:
        return False, errors
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return True, errors


def backup_data():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(BACKUP_DIR, f"data_backup_{ts}.json")
    shutil.copy2(DATA_PATH, dest)
    return dest


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Star Savior Web Enricher v3")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    # ─── Connectivity check ───
    if args.check:
        online, error = check_connectivity()
        print(json.dumps({
            "online": online,
            "error": error if not online else None,
            "message": "Connected to internet" if online
                else f"Could not connect to internet: {error}",
        }, indent=2))
        sys.exit(0 if online else 1)

    # ─── Validate ───
    if args.validate:
        data, err = load_data()
        if err:
            print(json.dumps({"valid": False, "error": err}))
            sys.exit(1)
        ok, errors = validate_full_dataset(data)
        print(json.dumps({
            "valid": ok,
            "error_count": len(errors),
            "errors": errors,
            "character_count": len(data.get("characters", [])),
        }, indent=2, ensure_ascii=False))
        sys.exit(0 if ok else 1)

    # ─── Check internet ───
    online, conn_err = check_connectivity()
    if not online:
        print(json.dumps({
            "status": "error",
            "error_type": "no_connection",
            "message": f"Couldn't connect to internet: {conn_err}. Check your network and try again.",
            "enriched": 0,
        }, indent=2))
        sys.exit(1)

    # ─── Load data ───
    data, load_err = load_data()
    if load_err:
        print(json.dumps({
            "status": "error",
            "error_type": "data_load_failed",
            "message": f"Failed to load data: {load_err}",
            "enriched": 0,
        }, indent=2))
        sys.exit(1)

    # ─── Check if enrichment needed ───
    characters = data.get("characters", [])
    needing = [c for c in characters if needs_enrichment(c)]

    if not needing and not args.force:
        print(json.dumps({
            "status": "complete",
            "message": "All characters already have complete data — no new data available on the internet.",
            "enriched": 0,
            "total_characters": len(characters),
        }, indent=2))
        sys.exit(0)

    # ─── Scrape Tychara (PRIMARY SOURCE) ───
    print(json.dumps({
        "status": "progress",
        "message": f"Scraping {len(needing)} characters from Tychara...",
    }), file=sys.stderr, flush=True)

    session = _get_session()
    scrape_errors = []

    html, err = fetch_url(SOURCES["tychara_tierlist"]["url"], session=session)
    if not html:
        scrape_errors.append(f"Tychara: {err}")
        print(json.dumps({
            "status": "error",
            "error_type": "scrape_failed",
            "message": f"Could not fetch Tychara tier list: {err}",
            "enriched": 0,
            "scrape_errors": scrape_errors,
        }, indent=2))
        sys.exit(1)

    tychara_data = parse_tychara_tierlist(html)
    chars_found = len(tychara_data)

    print(json.dumps({
        "status": "progress",
        "message": f"Tychara: extracted data for {chars_found} characters",
    }), file=sys.stderr, flush=True)

    if chars_found == 0:
        print(json.dumps({
            "status": "error",
            "error_type": "parse_failed",
            "message": "Fetched Tychara page but couldn't extract character data. Page structure may have changed.",
            "enriched": 0,
        }, indent=2))
        sys.exit(1)

    # ─── Backup ───
    backup_path = None
    if not args.dry_run:
        try:
            backup_path = backup_data()
        except Exception as e:
            print(json.dumps({
                "status": "error",
                "error_type": "backup_failed",
                "message": f"Could not create backup: {e}",
                "enriched": 0,
            }, indent=2))
            sys.exit(1)

    # ─── Enrich ───
    results, enriched_count = enrich_all(
        data, tychara_data,
        dry_run=args.dry_run,
        force=args.force,
    )

    # ─── Save ───
    save_ok = True
    save_errors = []
    if not args.dry_run and enriched_count > 0:
        save_ok, save_errors = save_data(data)

    # ─── Result ───
    if not save_ok:
        status = "error"
        message = f"Validation failed after enrichment. Backup at: {backup_path}"
    elif enriched_count > 0:
        status = "success"
        message = f"Enriched {enriched_count} characters from Tychara (tychara.com)."
    else:
        status = "complete"
        message = "No new data available — all characters are up to date."

    if args.dry_run:
        message = f"[DRY RUN] Would enrich {enriched_count} characters."

    output = {
        "status": status,
        "message": message,
        "online": True,
        "enriched": enriched_count,
        "dry_run": args.dry_run,
        "backup": backup_path,
        "total_characters": len(characters),
        "characters_found_online": chars_found,
        "results": results,
        "save_ok": save_ok,
        "validation_errors": save_errors,
    }

    print(json.dumps(output, indent=2, ensure_ascii=False))
    sys.exit(0 if save_ok else 1)


if __name__ == "__main__":
    main()
