# ⭐ Star Savior Meta Tool

![Version](https://img.shields.io/badge/Version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)
![Backend](https://img.shields.io/badge/Backend-Python_3-yellow.svg)
![Frontend](https://img.shields.io/badge/Frontend-.NET_8_WPF-purple.svg)

**Star Savior Meta Tool** is a premier, desktop meta-reasoning engine designed for competitive team building. Rather than relying on simple subjective tier lists, this tool uses a dynamic synergy logic engine driven by a hybrid architecture (WPF Frontend + Python Backend) to mathematically score and suggest optimal team compositions based on character tags, roles, and elements.

---

## 🔥 Key Features

### 1. Advanced Team Builder (No-Hallucination Engine)
Our Auto-Fix engine dynamically scores all available units to recommend replacements based strictly on raw data from `data.json`:
* **Mathematical Weighting:** Base Tier Points (T0 = 100) + Elemental Matches (+15/45) + Tag Synergy (+25).
* **Focus Modes:**
  * ⚖️ **Balanced:** 1 DPS, 1 Support, 1 Defender.
  * ⚔️ **Hyper Carry:** 1 Main DPS + 2-3 Supports (Buff/Cleanse priority).
  * ⏳ **Stall:** Resilient composition (Shield/Sustain priority).
  * ⚡ **Burst Speed:** Aggressive assault (Energy/Burst priority).
  * 🎯 **Control:** Lockdown tactics (Debuff/AoE priority).
  * 🌟 **Elemental:** Strict same-element resonance enforcement.
* **Class & Elemental Synergies:** The tool actively parses and rewards bonuses like "Mastery of Fire" or "Dual Support" healing buffs.

### 2. Tier List Explorer
A visually stunning, smooth WPF frontend to view and filter characters across roles, elements, and tiers (T0 -> B-Tier).

### 3. Online Data Enricher
Instead of entering unit synergies manually, the Python subsystem actively scrapes verified data targets (like Tychara JSON-LD) to recursively gather lore, `why_meta` reasons, and detailed element traits.

---

## 🏗️ Architecture

The app is built utilizing a cutting-edge hybrid infrastructure:
* **The Interface (C# / .NET 8 WPF):** A premium, dark-mode MVVM application handling state, binding, animations, and rendering.
* **The Engine (Python 3):** Complex text-parsing, scraping, and combinatorics calculation are delegated to Python scripts (`data_engine.py`, `team_builder.py`, `meta_scorer.py`, `web_enricher.py`).
* **The Bridge (`PythonBridge.cs`):** Seamlessly executes the Python subsystem, capturing raw JSON output and interpreting it via C# Data Models for the UI to consume instantly.

---

## 🚀 Installation & Usage

### Option 1: Standalone Build (Recommended for Users)
You do not need to install Python or .NET to use the tool if you download the official Release package!
1. Go to the [Releases](https://github.com/Eustakius/StarSaviorMetaTool/releases) tab on GitHub.
2. Download `StarSaviorTool_Release.zip`.
3. Extract the folder to your PC and double-click `StarSaviorTool.exe`.

### Option 2: Running from Source (For Developers)
1. Ensure both **.NET 8 SDK** and **Python 3** are installed.
2. Clone the repository: `git clone https://github.com/Eustakius/StarSaviorMetaTool.git`
3. Enter the project: `cd StarSaviorMetaTool/StarSaviorTool`
4. Install Python dependencies (only required for the Enricher): `pip install requests beautifulsoup4`
5. Run the app: `dotnet run`

---

## 🗄️ Project Structure
* `/StarSaviorTool/` - The C# .NET WPF source code.
* `/python/` - The Python backend scripts (routing logic, scrapers, and AI builders).
* `data.json` - The localized, single-source-of-truth database for all character specs.
* `soul.md` - Technical framework documentation.

---

*Enjoy building the ultimate Meta Teams!*
