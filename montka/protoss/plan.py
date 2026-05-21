import random

from sc2.data import Race

from ares.behaviors.macro import MacroPlan

from montka.protoss.builds import BUILDS
from montka.protoss.macro import Macro
from montka.protoss.production import Production
from montka.protoss.combat import Combat
from montka.protoss.defense import Defense
from montka.protoss.micro import MICRO


class ProtossPlan:
    def __init__(self, ai, enemy_race: Race):
        self.ai = ai
        self.enemy_race = enemy_race
        self._config: dict = {}
        self._macro: Macro = None
        self._production: Production = None
        self._combat: Combat = None
        self._defense: Defense = None

    async def on_start(self) -> None:
        # Pick a build weighted randomly, filtered to those good against the enemy race.
        # Falls back to all builds if none match the enemy race specifically.
        candidates = [b for b in BUILDS if not b.good_against or self.enemy_race in b.good_against]
        if not candidates:
            candidates = BUILDS
        chosen = random.choices(candidates, weights=[b.weight for b in candidates])[0]
        self._config = chosen.fn()

        self._macro = Macro(self.ai, self._config)
        self._production = Production(self.ai, self._config)
        self._combat = Combat(self.ai, self._config)
        self._defense = Defense(self.ai, self._config)

    async def on_step(self, iteration: int) -> None:
        # MacroPlan is a single shared waterfall — all mineral-spending behaviors
        # across modules are added to it in priority order, then registered once.
        # This ensures the correct global mineral priority: macro first, then production.
        macro = MacroPlan()
        self._macro.add_behaviors(macro)
        self._production.add_behaviors(macro)
        self.ai.register_behavior(macro)

        # Non-spending behaviors (gas, chrono, mining) are registered separately
        # inside each module so they always run regardless of mineral budget.
        self._macro.on_step()
        self._combat.on_step()
        self._defense.on_step()

        # Run micro modules — each handles its unit types independently of the
        # attack state machine so Blink-retreat works during rallying too.
        for module in MICRO:
            units = self.ai.units(module.unit_types).ready
            if units:
                module.run(self, units)
