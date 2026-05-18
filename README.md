# SC2 Bots

Two Protoss StarCraft II ladder bots built on [ares-sc2](https://github.com/AresSC2/ares-sc2) and [python-sc2 (burnysc2)](https://github.com/BurnySc2/python-sc2). Same framework, same race, very different play styles.

## The bots

### Mont'ka — fast and aggressive
Tight tech path, low base count, hits the opponent before they finish setting up. Built around an early attack wave and tempo. If the first push doesn't break, things get spicy.

### Kau'yon — slow and macro-heavy
Plays the long game. Expands hard, builds a deeper economy, takes the full upgrade ladder, and only commits to a fight once the army is well past critical mass. Patient and grindy.

---

## Run locally

```
python -m venv venv
venv\Scripts\activate
pip install -e "git+https://github.com/AresSC2/ares-sc2.git#egg=ares-sc2"
python run_custom.py
```

Edit `run_custom.py` to pick map, difficulty, and which bot to run.

---

## Packaging

`package_bot.py` builds either bot into an AI Arena compatible zip:

```
python package_bot.py --bot kauyon
python package_bot.py --bot montka
```

Output: `publish/Kauyon.zip` or `publish/Montka.zip`.