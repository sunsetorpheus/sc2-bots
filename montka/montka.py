import random
from typing import Optional

from ares import AresBot
from sc2.data import Race


CHOSEN_RACE = random.choice([Race.Terran, Race.Zerg, Race.Protoss])


class Montka(AresBot):
    def __init__(self, game_step_override: Optional[int] = None):
        super().__init__(game_step_override)
        self._race_plan = None

    async def on_start(self) -> None:
        await super().on_start()

        enemy_race = self.enemy_race

        if self.race == Race.Protoss:
            from montka.protoss.plan import ProtossPlan
            self._race_plan = ProtossPlan(self, enemy_race)
        elif self.race == Race.Terran:
            from montka.terran.plan import TerranPlan
            self._race_plan = TerranPlan(self, enemy_race)
        else:
            from montka.zerg.plan import ZergPlan
            self._race_plan = ZergPlan(self, enemy_race)

        await self._race_plan.on_start()

    async def on_step(self, iteration: int) -> None:
        await super().on_step(iteration)
        if self._race_plan:
            await self._race_plan.on_step(iteration)


def run():
    from sc2.player import Bot
    return Bot(CHOSEN_RACE, Montka())
