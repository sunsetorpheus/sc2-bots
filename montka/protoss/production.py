from sc2.dicts.unit_trained_from import UNIT_TRAINED_FROM
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId

from ares.behaviors.macro import MacroPlan, SpawnController

from common.behaviors import UpgradeController


class Production:
    def __init__(self, ai, config: dict):
        self.ai = ai
        self.config = config

    def add_behaviors(self, macro: MacroPlan) -> None:
        # Add all production behaviors to the shared MacroPlan.
        # Called by plan.py after macro behaviors so macro always has priority.
        self._upgrades(macro)
        self._spawn_fixed_count()
        self._spawn_units(macro)

    def _upgrades(self, macro: MacroPlan) -> None:
        # Collect all upgrades to research in priority order.
        # Warpgate always goes first — most impactful early research.
        # After that: weapons 1-2-3 then armor 1-2-3 by default.
        # Build files can add extra upgrades (e.g. Blink) via "upgrades" in config.
        if not self.ai.structures(UnitTypeId.CYBERNETICSCORE).ready:
            return

        # Warpgate: converts Gateways to instant warp-in near any Pylon.
        upgrades = [UpgradeId.WARPGATERESEARCH]

        # Interleaved weapons/armor so two Forges research in parallel.
        upgrades += [
            UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1,
            UpgradeId.PROTOSSGROUNDARMORSLEVEL1,
            UpgradeId.PROTOSSGROUNDWEAPONSLEVEL2,
            UpgradeId.PROTOSSGROUNDARMORSLEVEL2,
            UpgradeId.PROTOSSGROUNDWEAPONSLEVEL3,
            UpgradeId.PROTOSSGROUNDARMORSLEVEL3,
        ]

        # Build-specific extras — e.g. Blink for Stalker builds (requires Twilight Council).
        upgrades += self.config.get("upgrades", [])

        # auto_tech_up_enabled=False prevents UpgradeController from building
        # upgrade structures on its own — Forge and Twilight are handled in macro.py.
        macro.add(UpgradeController(
            upgrade_list=upgrades,
            base_location=self.ai.start_location,
            auto_tech_up_enabled=False,
        ))

    def _spawn_fixed_count(self) -> None:
        # Pre-pass for units with a "count" key in army_comp — build exactly that many
        # before SpawnController runs for proportion-based units. Runs outside MacroPlan
        # so it doesn't compete with the mineral waterfall.
        army_comp: dict = self.config.get("army_comp", {})
        ai = self.ai

        for unit_type, info in sorted(army_comp.items(), key=lambda x: x[1].get("priority", 0)):
            target_count = info.get("count")
            if target_count is None:
                continue  # proportion-based unit, handled by SpawnController

            if not ai.tech_ready_for_unit(unit_type):
                continue  # skip if tech building not ready yet

            current = ai.units(unit_type).amount
            if current >= target_count:
                continue  # already at or above target

            if not ai.can_afford(unit_type):
                continue  # can't afford, skip rather than block lower-priority units

            # Look up which structure(s) produce this unit — covers gateways, robo,
            # stargates, or any other production building automatically.
            trained_from: set = UNIT_TRAINED_FROM.get(unit_type, set())

            for structure_type in trained_from:
                # Warpgate is a morphed Gateway — use warp-in instead of train.
                if structure_type == UnitTypeId.GATEWAY:
                    warpgates = ai.structures(UnitTypeId.WARPGATE).ready
                    if warpgates:
                        ai.mediator.request_warp_in(
                            build_from=warpgates.first,
                            unit_type=unit_type,
                            target=None,  # warp_in_manager defaults to start_location
                        )
                        break
                    # Warpgate research not done yet — fall through to train from Gateway.
                    structure_type = UnitTypeId.GATEWAY

                building = ai.structures(structure_type).ready.idle
                if building:
                    building.first.train(unit_type)
                    break

    def _spawn_units(self, macro: MacroPlan) -> None:
        # army_comp is defined per build — no global default since different builds
        # produce different units. If not set, production does nothing.
        army_comp: dict = self.config.get("army_comp")
        if not army_comp:
            return

        # Gate on at least one Gateway or Warpgate being ready before trying to spawn.
        has_gate = (
            self.ai.structures(UnitTypeId.GATEWAY).ready
            or self.ai.structures(UnitTypeId.WARPGATE).ready
        )
        if not has_gate:
            return

        # Only pass proportion-based units to SpawnController — count-based units are
        # handled by _spawn_fixed_count and excluded here to avoid proportion assertion errors.
        proportion_comp = {k: v for k, v in army_comp.items() if "proportion" in v}
        if not proportion_comp:
            return

        macro.add(SpawnController(army_composition_dict=proportion_comp))
