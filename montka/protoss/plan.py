import random
from sc2.data import Race
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId

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

from montka.protoss.builds import BUILDS


class ProtossPlan:
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
        gateway_target: int = cfg.get("gateway_target", 8)
        probe_max: int = cfg.get("probe_max", 75)
        expand_to: int = cfg.get("expand_to", 3)

        macro = MacroPlan()

        # Always keep supply topped up.
        macro.add(AutoSupply(base_location=ai.start_location))

        # Workers — cap at probe_max.
        macro.add(BuildWorkers(to_count=probe_max))

        # Gas — 2 assimilators per base.
        macro.add(GasBuildingController(to_count=len(ai.townhalls) * 2))

        # Expansion.
        macro.add(ExpansionController(to_count=expand_to))

        # Opener structures: Gateway → Cybernetics Core → more Gateways.
        if not ai.structures(UnitTypeId.GATEWAY).ready:
            macro.add(
                BuildStructure(
                    base_location=ai.start_location,
                    structure_id=UnitTypeId.GATEWAY,
                    to_count=1,
                )
            )
        elif not ai.structures(UnitTypeId.CYBERNETICSCORE).ready:
            macro.add(
                BuildStructure(
                    base_location=ai.start_location,
                    structure_id=UnitTypeId.CYBERNETICSCORE,
                    to_count=1,
                )
            )
        else:
            # Scale up gateways toward the target count.
            current_gates = len(ai.structures(UnitTypeId.GATEWAY))
            if current_gates < gateway_target:
                macro.add(
                    BuildStructure(
                        base_location=ai.start_location,
                        structure_id=UnitTypeId.GATEWAY,
                        to_count=gateway_target,
                    )
                )

        # Upgrades (Warp Gate first, then weapon/armor).
        if upgrades and ai.structures(UnitTypeId.CYBERNETICSCORE).ready:
            macro.add(
                UpgradeController(
                    upgrade_list=upgrades,
                    base_location=ai.start_location,
                )
            )

        # Army production.
        if army_comp and ai.structures(UnitTypeId.GATEWAY).ready:
            macro.add(SpawnController(army_composition_dict=army_comp))

        ai.register_behavior(macro)
