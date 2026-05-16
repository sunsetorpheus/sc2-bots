"""
Local test runner for Montka.
Launches a game vs the built-in AI using python-sc2's sc2.main.run_game.
"""
import sc2
from sc2 import maps
from sc2.data import Difficulty, Race
from sc2.player import Bot, Computer

from montka.montka import CHOSEN_RACE, Montka


def main():
    sc2.run_game(
        maps.get("AcropolisLE"),
        [
            Bot(CHOSEN_RACE, Montka()),
            Computer(Race.Random, Difficulty.Medium),
        ],
        realtime=False,
    )


if __name__ == "__main__":
    main()
