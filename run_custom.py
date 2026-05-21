"""
Local test runner. Launches a game vs the built-in AI using python-sc2's sc2.main.run_game.
Flip BOT to switch between Montka and Kauyon.
"""
from sc2 import maps
from sc2.data import Difficulty, Race
from sc2.main import run_game
from sc2.player import Bot, Computer

from kauyon.kauyon import Kauyon
from montka.montka import Montka

# --- Options ---
BOT = "kauyon"                   # "montka" | "kauyon"
BOT_RACE = Race.Protoss          # Race.Protoss | Race.Terran | Race.Zerg | Race.Random
OPPONENT_RACE = Race.Random      # Race.Protoss | Race.Terran | Race.Zerg | Race.Random
DIFFICULTY = Difficulty.CheatInsane   # Easy | Medium | MediumHard | Hard | Harder | VeryHard | CheatVision | CheatMoney | CheatInsane
MAP = "PylonAIE_v4"                 # Any installed map name
REALTIME = False                 # True = watch at normal speed in SC2 window
# ---------------

BOTS = {"montka": Montka, "kauyon": Kauyon}


def main():
    bot_cls = BOTS[BOT]
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
