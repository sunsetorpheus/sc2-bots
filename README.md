# Montka — SC2 Bot

A multi-race StarCraft II bot built on [ares-sc2](https://github.com/AresSC2/ares-sc2) and [python-sc2 (burnysc2)](https://github.com/BurnySc2/python-sc2).

The bot randomly selects a race each game for unpredictability.

---

## Getting started

### 1. Prerequisites

- [Python 3.11](https://www.python.org/downloads/)
- StarCraft II installed locally (for testing)
- Git

### 2. Clone the repo

```
git clone https://github.com/sunsetorpheus/sc2-bot-montka.git <BotName>
cd <BotName>
```

### 3. Create and activate a virtual environment

```
python -m venv venv
venv\Scripts\activate
```

### 4. Install dependencies

```
pip install -e "git+https://github.com/AresSC2/ares-sc2.git#egg=ares-sc2"
```

Then fix the `.pth` file so the `sc2_helper` extension is found. Edit `venv\Lib\site-packages\ares_sc2.pth` to contain both lines:

```
<absolute-path-to-venv>/src/ares-sc2/src
<absolute-path-to-venv>/src/ares-sc2
```

---

## Run the bot locally (vs built-in AI)

```
python run_custom.py
```

Launches a game on AcropolisLE vs Medium AI. Edit `run_custom.py` to change the map or difficulty.

Replays are saved to `games/` automatically by SC2.

---

## Rename the bot

### 1. Rename the bot folder

Rename `montka/` to your bot name (lowercase, no spaces), e.g. `mybot/`.

### 2. Update the main class (`montka/montka.py`)

Rename the file to `mybot.py` and update the class name and imports:

```python
class MyBot(AresBot):
    ...
```

### 3. Update `montka/run.py`

```python
# Change
from montka.montka import run
# To
from mybot.mybot import run
```

### 4. Update `run_custom.py`

```python
# Change
from montka.montka import CHOSEN_RACE, Montka
# To
from mybot.mybot import CHOSEN_RACE, MyBot
```

---

## Add a new build

1. Create a file in `montka/{race}/builds/yourname.py` — define a `_config()` function returning a dict and a `Build(...)` instance
2. Register it in `montka/{race}/builds/__init__.py`
3. The plan picks it automatically using weighted-random matchup-aware selection

---

## Publish to AI Arena

Publishing is handled automatically by GitHub Actions on every push to `master`.

### Setup (one time)

1. Push the repo to GitHub
2. Go to **Settings → Secrets and variables → Actions** and add:
   - `AIARENA_API_TOKEN` — from [aiarena.net/profile/token](https://aiarena.net/profile/token)
   - `AIARENA_BOT_ID` — the numeric ID shown on your bot's page on aiarena.net
3. Create your bot on aiarena.net (**My Bots → Create Bot**, Type = Python, Plays = Random)

### How it works

Every push to `master` triggers `.github/workflows/ladder_zip.yml` which:
1. Runs on `ubuntu-latest` (same OS as AI Arena servers)
2. Clones `python-sc2`, `SC2MapAnalysis`, `cython-extensions-sc2`, and `ares-sc2`
3. Compiles `cython_extensions` natively for Linux
4. Packages everything into `publish/Montka.zip`
5. Uploads the zip to AI Arena via API

The build artifact is also available for download under **Actions → latest run**.

### Manual upload

If you want to upload manually without GitHub Actions:
- Download the zip from the Actions artifact
- Upload it on aiarena.net under **My Bots → your bot → Upload new zip**

> **Do not** use `python package_bot.py` to generate a zip for upload — it runs on Windows and produces Linux-incompatible binaries. Only the GitHub Actions build (Ubuntu) produces a working zip.

---

## Project structure

```
montka/                  # Bot code (rename this to your bot name)
  montka.py              # Main bot class (AresBot, random race)
  run.py                 # Ladder entry point (AI Arena / sc2ai compatible)
  protoss/
    plan.py              # ProtossPlan — registers ares behaviors each step
    common.py            # Shared constants (army comps, upgrade lists)
    build.py             # Build dataclass
    builds/
      __init__.py        # BUILDS list
      stalker.py         # Mass Stalker build config
  terran/
    plan.py              # TerranPlan
    common.py
    build.py
    builds/
      __init__.py
      bio.py             # Bio aggression build config
  zerg/
    plan.py              # ZergPlan
    common.py
    build.py
    builds/
      __init__.py
      roach.py           # Roach/Ravager build config
run.py                   # Ladder entry point (root, called by AI Arena)
run_custom.py            # Local testing entry point (vs built-in AI)
config.yml               # ares-sc2 settings
requirements.txt         # Python dependencies
package_bot.py           # Local packaging script (structure check only)
scripts/
  upload_to_aiarena.py   # Used by GitHub Actions to upload the zip
.github/workflows/
  ladder_zip.yml         # CI: build zip on Ubuntu and upload to AI Arena
```

---

## Documentation

- [ares-sc2 docs](https://aressc2.github.io/ares-sc2/index.html)
- [python-sc2 (burnysc2)](https://github.com/BurnySc2/python-sc2)
- [AI Arena](https://aiarena.net)
