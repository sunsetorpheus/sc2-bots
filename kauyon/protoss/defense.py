from sc2.ids.unit_typeid import UnitTypeId
from sc2.unit import Unit

from ares.behaviors.macro import BuildStructure, MacroPlan

from kauyon.protoss.common import DEFENSE_RADIUS, MAX_BATTERIES_PER_BASE, MAX_CANNONS_PER_BASE


class Defense:
    def __init__(self, ai, config: dict):
        self.ai = ai
        self.config = config

    def on_step(self) -> None:
        for nexus in self.ai.townhalls.ready:
            if self._base_is_under_attack(nexus):
                self._build_defenses(nexus)

    def _base_is_under_attack(self, nexus: Unit) -> bool:
        # Check if any friendly unit or structure within range of this Nexus
        # is actively taking damage. More reliable than checking Nexus alone
        # since workers or units are often targeted first.
        radius = self.config.get("defense_radius", DEFENSE_RADIUS)
        nearby_friendly = (
            self.ai.units.closer_than(radius, nexus)
            | self.ai.structures.closer_than(radius, nexus)
        )
        return any(u.is_under_attack for u in nearby_friendly)

    def _build_defenses(self, nexus: Unit) -> None:
        has_forge = bool(self.ai.structures(UnitTypeId.FORGE).ready)
        has_gateway = bool(self.ai.structures(UnitTypeId.GATEWAY).ready)

        radius = self.config.get("defense_radius", DEFENSE_RADIUS)
        max_cannons = self.config.get("max_cannons_per_base", MAX_CANNONS_PER_BASE)
        max_batteries = self.config.get("max_batteries_per_base", MAX_BATTERIES_PER_BASE)

        # Count existing defenses near this Nexus.
        cannons_nearby = len(self.ai.structures(UnitTypeId.PHOTONCANNON).closer_than(radius, nexus))
        batteries_nearby = len(self.ai.structures(UnitTypeId.SHIELDBATTERY).closer_than(radius, nexus))

        # Each base gets its own MacroPlan so defensive spending is isolated
        # from the main macro waterfall and doesn't block probe/gate production.
        macro = MacroPlan()

        # Cannons require a Forge — capped at max_cannons per base.
        if has_forge and cannons_nearby < max_cannons:
            macro.add(BuildStructure(
                base_location=nexus.position,
                structure_id=UnitTypeId.PHOTONCANNON,
                to_count=cannons_nearby + 1,
            ))

        # Shield Batteries require a Gateway — capped at max_batteries per base.
        if has_gateway and batteries_nearby < max_batteries:
            macro.add(BuildStructure(
                base_location=nexus.position,
                structure_id=UnitTypeId.SHIELDBATTERY,
                to_count=batteries_nearby + 1,
            ))

        if macro:
            self.ai.register_behavior(macro)
