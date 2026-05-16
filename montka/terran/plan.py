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
    UpgradeCCs,
)

from montka.terran.builds import BUILDS


class TerranPlan:
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
        barracks_target: int = cfg.get("barracks_target", 5)
        scv_max: int = cfg.get("scv_max", 70)
        expand_to: int = cfg.get("expand_to", 3)

        macro = MacroPlan()

        # Supply depots.
        macro.add(AutoSupply(base_location=ai.start_location))

        # Workers.
        macro.add(BuildWorkers(to_count=scv_max))

        # Orbital Command upgrades.
        macro.add(UpgradeCCs(to=UnitTypeId.ORBITALCOMMAND))

        # Gas — 2 refineries per base.
        macro.add(GasBuildingController(to_count=len(ai.townhalls) * 2))

        # Expansion.
        macro.add(ExpansionController(to_count=expand_to))

        # Opener: Barracks first.
        if not ai.structures(UnitTypeId.BARRACKS).ready:
            macro.add(
                BuildStructure(
                    base_location=ai.start_location,
                    structure_id=UnitTypeId.BARRACKS,
                    to_count=1,
                )
            )
        else:
            # Factory for tech (Marauder).
            if not ai.structures(UnitTypeId.FACTORY).ready:
                macro.add(
                    BuildStructure(
                        base_location=ai.start_location,
                        structure_id=UnitTypeId.FACTORY,
                        to_count=1,
                    )
                )
            # Starport for Medivacs.
            if not ai.structures(UnitTypeId.STARPORT).ready:
                macro.add(
                    BuildStructure(
                        base_location=ai.start_location,
                        structure_id=UnitTypeId.STARPORT,
                        to_count=1,
                    )
                )
            # Scale up barracks.
            current_rax = len(ai.structures(UnitTypeId.BARRACKS))
            if current_rax < barracks_target:
                macro.add(
                    BuildStructure(
                        base_location=ai.start_location,
                        structure_id=UnitTypeId.BARRACKS,
                        to_count=barracks_target,
                    )
                )

        # Upgrades.
        if upgrades and ai.structures(UnitTypeId.BARRACKS).ready:
            macro.add(
                UpgradeController(
                    upgrade_list=upgrades,
                    base_location=ai.start_location,
                )
            )

        # Army.
        if army_comp and ai.structures(UnitTypeId.BARRACKS).ready:
            macro.add(SpawnController(army_composition_dict=army_comp))

        ai.register_behavior(macro)
