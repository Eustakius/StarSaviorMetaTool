
# SOUL.md

## Star Savior Meta Tool — Hybrid C# + Embedded Python Architecture

---

## 🧠 CORE RULE (NON-NEGOTIABLE)

> Every piece of data in this application MUST originate from verified sources.

### Approved Sources:

* Tychara Tier List (Mar 2026)
* User-provided dataset (PVE Tier + Character Notes) 
* KR/JP meta references (if added later)

---

## 🏗️ ARCHITECTURE OVERVIEW

```
┌──────────────────────────────────────────┐
│         C# WPF Desktop Application       │
│  ┌────────────────────────────────────┐   │
│  │  UI Layer (XAML + WPF Controls)    │   │
│  │  • Tier List Grid View             │   │
│  │  • Character Detail Panel          │   │
│  │  • Team Builder Interface          │   │
│  │  • Meta Score Dashboard            │   │
│  └──────────────┬─────────────────────┘   │
│                 │ calls                    │
│  ┌──────────────▼─────────────────────┐   │
│  │  Python Engine (Embedded via       │   │
│  │  Process / pythonnet)              │   │
│  │  • data_engine.py                  │   │
│  │  • team_builder.py                 │   │
│  │  • meta_scorer.py                  │   │
│  └──────────────┬─────────────────────┘   │
│                 │ reads                    │
│  ┌──────────────▼─────────────────────┐   │
│  │  data.json (Single Source of Truth) │   │
│  └────────────────────────────────────┘   │
└──────────────────────────────────────────┘
```

### Layer Responsibilities:

| Layer | Tech | Responsibility |
|-------|------|----------------|
| **UI** | C# / WPF / XAML | Rendering, user interaction, theming |
| **Logic** | Python (embedded) | Data parsing, team suggestions, meta scoring |
| **Data** | JSON | Character database, tier system, versioning |

---

## 🚫 ZERO-HALLUCINATION POLICY

The system MUST NOT:

* Invent skill descriptions
* Assume character roles
* Generate "why meta" explanations
* Assign fake stats (DPS, scaling, etc.)

If data is missing:

> Display: `"Data unavailable — update required"`

---

## 📊 DATA EXTRACTION RULES

All character data must be parsed EXACTLY from source.

---

## 🧩 TIER SYSTEM (SOURCE-LOCKED)

### From Tychara + Dataset:

#### T0 (God Tier)

* Bunnygirl Charlotte
* Emilly
* Asherah (Waltz of Starlight)
* Lacy

#### SS

* Hilde
* Muriel
* Frey (Noble Princess)
* Bunnygirl Claire
* Bell Rhys

#### S

* Charlotte
* Kyra
* Petra
* Lugh
* Yoo Mina
* Roberta
* Dana
* Haydee
* Tanya
* Luna
* Seira
* Elisa
* Lydia

#### A

* Bunnygirl Scarlet
* Harley
* Serpang
* Asherah
* Epindel
* Lily
* Frey
* Omega
* Smile

#### B

* Annah
* Carmen
* Marcille
* Trish

---

## 🧠 CHARACTER DATA (STRICT EXTRACTION)

### Example (REAL — FROM SOURCE)

```json
{
  "name": "Bunnygirl Charlotte",
  "role": "Assassin",
  "tier": "T0",
  "why_meta": [
    "Grants 2-turn attack power increase buff to all allies",
    "Functions as both sub-dealer and main dealer",
    "Top-tier burst scaling"
  ],
  "weakness": [
    "Requires investment to reach full potential"
  ],
  "source": ["Tychara Mar 2026", "User dataset"]
}
```

---

## ⚠️ IMPORTANT: TEXT HANDLING

* Skill descriptions must be **copied or lightly cleaned**
* Grammar fixes allowed
* Meaning MUST remain unchanged

---

## 🧩 TEAM BUILDER LOGIC (SOURCE-BASED ONLY)

### Allowed Inputs:

* Tier
* Role
* Explicit synergy (if defined)

### NOT allowed:

* "This character is best with X" (unless defined)
* AI assumptions

---

### VALID TEAM LOGIC (Python Engine)

```python
def suggest_team(selected, data):
    team = set(selected)

    # Fill missing roles based on tier priority
    if not has_role(team, "Support"):
        team.add(find_best_by_role("Support", data))

    if not has_role(team, "Defender"):
        team.add(find_best_by_role("Defender", data))

    return team
```

---

## 📊 META SCORING (NO FAKE STATS)

Use tier-only weighting (Python Engine):

```python
TIER_WEIGHT = {
    "T0": 5,
    "SS": 4,
    "S": 3,
    "A": 2,
    "B": 1
}
```

---

## 🔍 CHARACTER PANEL REQUIREMENTS

Each character MUST display:

* Name
* Tier
* Role
* Element (if available)
* Why Meta (from source)
* Weakness (from source)

---

## 🔗 SOURCE TRACEABILITY (MANDATORY)

Each character must include:

* `"source": ["Tychara", "User Dataset"]`

UI should show:

> 📌 Source: Tychara (Mar 2026)

---

## 📁 PROJECT STRUCTURE

```
/starsaviortools
  ├── data.json              (all characters — single source of truth)
  ├── soul.md                (this file — project rules)
  ├── StarSaviorTool/        (C# WPF project)
  │   ├── StarSaviorTool.csproj
  │   ├── App.xaml / App.xaml.cs
  │   ├── MainWindow.xaml / MainWindow.xaml.cs
  │   ├── Models/
  │   │   └── Character.cs
  │   ├── ViewModels/
  │   │   └── MainViewModel.cs
  │   ├── Views/
  │   │   ├── TierListView.xaml
  │   │   ├── CharacterDetailView.xaml
  │   │   └── TeamBuilderView.xaml
  │   └── Services/
  │       └── PythonBridge.cs
  └── python/
      ├── data_engine.py     (load & filter characters)
      ├── team_builder.py    (team suggestion logic)
      └── meta_scorer.py     (tier-weight scoring)
```

---

## 🚀 UPDATE SYSTEM

* Replace `data.json` → app auto-updates
* No code changes required
* Version tag required:

```json
"meta_version": "2026.03"
```

---

## ⚠️ EDGE CASE HANDLING

If:

* Character exists in tier list but no notes
  → mark as:

```json
"why_meta": ["No detailed data available"]
```

---

## 🧠 DESIGN PHILOSOPHY

> "This is a META TOOL, not a GUESSING TOOL."

* Accuracy > completeness
* Source > assumption
* Verified > generated

---

## ✅ FINAL GOAL

A system where:

* Every suggestion can be traced
* Every explanation is verifiable
* No fake data exists

---

## 🔥 SMART TEAM BUILDER LOGIC (FINAL EVOLUTION)

> Not a tier list tool. A **meta reasoning engine**.

### Core Evaluation Layers:

1. **Role coverage** (structure)
2. **Tier strength** (power)
3. **Functional coverage** (abilities, weaknesses, meta reasons)

---

### 🧩 FUNCTION TAG SYSTEM

Each character has `tags` extracted from verified data:

```json
{
  "name": "Bunnygirl Charlotte",
  "role": "Assassin",
  "tier": "T0",
  "tags": ["attack_buff", "burst_dps", "sub_dealer"]
}
```

---

### 🧠 TEAM REQUIREMENTS (REAL META NEEDS)

| Requirement | Why |
|---|---|
| Damage | You need to kill |
| Sustain (heal/shield) | Prevent wipe |
| Cleanse | Remove debuffs |
| Buff/Debuff | Amplify damage |
| Control (optional) | Freeze, slow |

---

### ⚙️ COVERAGE ENGINE

```python
def evaluate_team(team):
    coverage = set()
    for char in team:
        coverage.update(char["tags"])
    return coverage
```

---

### 🚨 WEAKNESS DETECTION

```python
REQUIRED_TAGS = ["burst_dps", "heal", "damage_mitigation"]

def find_weaknesses(coverage):
    missing = []
    for tag in REQUIRED_TAGS:
        if tag not in coverage:
            missing.append(tag)
    return missing
```

---

### 🔥 AUTO-FIX TEAM

```python
def fix_team(team, data):
    coverage = evaluate_team(team)
    missing = find_weaknesses(coverage)
    for need in missing:
        best = find_character_with_tag(need, data)
        team.add(best)
    return team
```

---

### 🧠 EXPLANATION GENERATOR (NO HALLUCINATION)

Build explanation from data, not AI:

```python
EXPLANATIONS = {
    "heal": "Provides sustain through healing",
    "cleanse": "Removes debuffs for team stability",
    "attack_buff": "Increases team damage output"
}

def explain_team(team):
    explanation = []
    for char in team:
        for tag in char["tags"]:
            explanation.append(EXPLANATIONS.get(tag, ""))
    return list(set(explanation))
```

---

### 🧠 SYSTEM ARCHITECTURE

```
User Input
   ↓
Role Engine
   ↓
Tier Filter
   ↓
Tag Coverage Engine
   ↓
Weakness Detector
   ↓
Auto Fix
   ↓
Explanation Generator
```

---

### 🎯 KEY DIFFERENCE

| Normal Tool | This App |
|---|---|
| Picks by tier | Builds by function |
| No explanation | Full reasoning |
| Static | Adaptive |
| Dumb | Smart |

---

END OF FILE

