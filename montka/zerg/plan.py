import random
from sc2.data import Race
from sc2.ids.unit_typeid import UnitTypeId

from ares.behaviors.macro import (
    AutoSupply,
    BuildStructure,
    BuildWorkers,
    ExpansionController,
    GasBuildingController,
    MacroPlan,
    SpawnController,
    UpgradeController,
)

from montka.zerg.builds import BUILDS


class ZergPlan:
    def __init__(self, ai, enemy_race: Race):
        self.ai = ai
        self.enemy_race = enemy_race
        self._config: dict = {}

    async def on_start(self) -> None:
        candidates = [b for b in BUILDS if not b.good_against or self.enemy_race in b.good_against]
        if not candidates:
            candidates = BUILDS
        weights = [b.weight for b in candidates]
        chosen = random.choices(candidates, weights=weights)[0]
        self._config = chosen.fn()

    async def on_step(self, iteration: int) -> None:
        ai = self.ai
        cfg = self._config
        army_comp: dict = cfg.get("army_comp", {})
        upgrades: list = cfg.get("upgrades", [])
        drone_max: int = cfg.get("drone_max", 70)
        expand_to: int = cfg.get("expand_to", 4)

        macro = MacroPlan()

        # Overlords.
        macro.add(AutoSupply(base_location=ai.start_location))

        # Drones.
        macro.add(BuildWorkers(to_count=drone_max))

        # Gas — extractors per hatchery.
        macro.add(GasBuildingController(to_count=len(ai.townhalls) * 2))

        # Expand.
        macro.add(ExpansionController(to_count=expand_to))

        # Tech buildings: Spawning Pool → Roach Warren.
        if not ai.structures(UnitTypeId.SPAWNINGPOOL).ready:
            macro.add(
                BuildStructure(
                    base_location=ai.start_location,
                    structure_id=UnitTypeId.SPAWNINGPOOL,
                    to_count=1,
                )
            )
        elif not ai.structures(UnitTypeId.ROACHWARREN).ready:
            macro.add(
                BuildStructure(
                    base_location=ai.start_location,
                    structure_id=UnitTypeId.ROACHWARREN,
                    to_count=1,
                )
            )

        # Upgrades (Glial Reconstitution requires Lair).
        if upgrades and ai.structures(UnitTypeId.ROACHWARREN).ready:
            macro.add(
                UpgradeController(
                    upgrade_list=upgrades,
                    base_location=ai.start_location,
                )
            )

        # Army production via larvae.
        if army_comp and ai.structures(UnitTypeId.ROACHWARREN).ready:
            macro.add(SpawnController(army_composition_dict=army_comp))

        ai.register_behavior(macro)
