"""
Local test runner. Launches a game using python-sc2's sc2.main.run_game.
Two modes:
  - BOT_VS_AI: one bot vs the built-in computer
  - BOT_VS_BOT: Montka vs Kauyon
Flip MODE to switch between them.
"""
from sc2 import maps
from sc2.data import Difficulty, Race
from sc2.main import run_game
from sc2.player import Bot, Computer

from kauyon.kauyon import Kauyon
from montka.montka import Montka

# --- Options ---
MODE = "bot_vs_ai"              # "bot_vs_ai" | "bot_vs_bot"

# bot_vs_ai options
BOT = "montka"                   # "montka" | "kauyon"
BOT_RACE = Race.Protoss          # Race.Protoss | Race.Terran | Race.Zerg | Race.Random
OPPONENT_RACE = Race.Random      # Race.Protoss | Race.Terran | Race.Zerg | Race.Random
DIFFICULTY = Difficulty.Hard  # VeryEasy | Easy | Medium | MediumHard | Hard | Harder | VeryHard | CheatVision | CheatMoney | CheatInsane

MAP = "PylonAIE_v4"             # installed maps: PylonAIE_v4
REALTIME = False                 # False = fastest speed | True = normal game speed
# ---------------


def main():
    if MODE == "bot_vs_bot":
        # Montka (player 1) vs Kauyon (player 2) — both Protoss.
        run_game(
            maps.get(MAP),
            [
                Bot(Race.Protoss, Montka()),
                Bot(Race.Protoss, Kauyon()),
            ],
            realtime=REALTIME,
        )
    else:
        # Single bot vs built-in AI.
        bot_cls = {"montka": Montka, "kauyon": Kauyon}[BOT]
        run_game(
            maps.get(MAP),
            [
                Bot(BOT_RACE, bot_cls()),
                Computer(OPPONENT_RACE, DIFFICULTY),
            ],
            realtime=REALTIME,
        )


if __name__ == "__main__":
    main()
