import argparse
import asyncio

from sc2 import maps
from sc2.data import Race, Difficulty
from sc2.main import play_from_websocket, run_game
from sc2.player import Bot, Computer
from sc2.portconfig import Portconfig

from montka.montka import CHOSEN_RACE, Montka


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--GamePort", type=int)
    parser.add_argument("--LadderServer", type=str, default="127.0.0.1")
    parser.add_argument("--StartPort", type=int)
    parser.add_argument("--RealTime", action="store_true")
    args, _ = parser.parse_known_args()

    if args.GamePort:
        start = args.StartPort
        portconfig = Portconfig(
            server_ports=[start + 2, start + 3],
            player_ports=[[start + 4, start + 5]],
        ) if start else Portconfig.contiguous_ports()
        ws = f"ws://{args.LadderServer}:{args.GamePort}/sc2api"
        asyncio.run(
            play_from_websocket(
                ws,
                Bot(CHOSEN_RACE, Montka()),
                args.RealTime,
                portconfig=portconfig,
            )
        )
    else:
        run_game(
            maps.get("AcropolisLE"),
            [Bot(CHOSEN_RACE, Montka()), Computer(Race.Random, Difficulty.VeryHard)],
            realtime=False,
        )


if __name__ == "__main__":
    main()
