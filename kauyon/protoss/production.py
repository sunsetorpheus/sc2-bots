from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId

from ares.behaviors.macro import MacroPlan, SpawnController, UpgradeController


class Production:
    def __init__(self, ai, config: dict):
        self.ai = ai
        self.config = config

    def add_behaviors(self, macro: MacroPlan) -> None:
        # Add all production behaviors to the shared MacroPlan.
        # Called by plan.py after macro behaviors so macro always has priority.
        self._upgrades(macro)
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

        # Default: weapons then armor — always researched regardless of build.
        # Requires Forge (built in macro.py after 3rd base).
        upgrades += [
            UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1,
            UpgradeId.PROTOSSGROUNDWEAPONSLEVEL2,
            UpgradeId.PROTOSSGROUNDWEAPONSLEVEL3,
            UpgradeId.PROTOSSGROUNDARMORSLEVEL1,
            UpgradeId.PROTOSSGROUNDARMORSLEVEL2,
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

    def _spawn_units(self, macro: MacroPlan) -> None:
        # army_comp is defined per build — no global default since different builds
        # produce different units. If not set, production does nothing.
        army_comp: dict = self.config.get("army_comp")
        if not army_comp:
            return

        # Gate on at least one Gateway being ready before trying to spawn.
        # SpawnController handles warpgate vs gateway production automatically.
        if not self.ai.structures(UnitTypeId.GATEWAY).ready:
            return

        macro.add(SpawnController(army_composition_dict=army_comp))
