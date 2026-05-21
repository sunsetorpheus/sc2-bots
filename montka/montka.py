from typing import Optional

from ares import AresBot
from sc2.data import Race


CHOSEN_RACE = Race.Protoss


class Montka(AresBot):
    def __init__(self, game_step_override: Optional[int] = None):
        super().__init__(game_step_override)
        self._race_plan = None

    async def on_start(self) -> None:
        await super().on_start()

        enemy_race = self.enemy_race

        from montka.protoss.plan import ProtossPlan
        self._race_plan = ProtossPlan(self, enemy_race)

        await self._race_plan.on_start()

    async def on_step(self, iteration: int) -> None:
        await super().on_step(iteration)
        if self._race_plan:
            await self._race_plan.on_step(iteration)


def run():
    from sc2.player import Bot
    return Bot(CHOSEN_RACE, Montka())
