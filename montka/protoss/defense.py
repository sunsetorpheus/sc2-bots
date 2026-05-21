from sc2.ids.unit_typeid import UnitTypeId
from sc2.unit import Unit
from sc2.units import Units

from ares.behaviors.macro import BuildStructure, MacroPlan

from montka.protoss.common import DEFENSE_RADIUS, MAX_BATTERIES_PER_BASE, MAX_CANNONS_PER_BASE


class Defense:
    def __init__(self, ai, config: dict):
        self.ai = ai
        self.config = config

    def on_step(self) -> None:
        army_comp: dict = self.config.get("army_comp", {})
        army: Units = self.ai.units(set(army_comp.keys())).ready if army_comp else None

        for nexus in self.ai.townhalls.ready:
            if self._base_is_under_attack(nexus):
                self._build_defenses(nexus)
                if army:
                    self._defend_with_army(army)

    def _defend_with_army(self, army: Units) -> None:
        base_threats: Units = self.ai.enemy_units.filter(
            lambda u: not u.is_structure
            and not u.is_mineral_field
            and not u.is_vespene_geyser
            and any(u.distance_to(th) < 30 for th in self.ai.townhalls)
        )
        if base_threats:
            for unit in army:
                unit.attack(base_threats.closest_to(unit))

    def _base_is_under_attack(self, nexus: Unit) -> bool:
        # Require both damaged friendlies AND visible enemy units nearby.
        # Damaged-only check fires on scout units passing by or mid-regen shields.
        radius = self.config.get("defense_radius", DEFENSE_RADIUS)
        threats = self.ai.enemy_units.filter(
            lambda u: not u.is_structure
            and not u.is_mineral_field
            and not u.is_vespene_geyser
            and u.distance_to(nexus) < radius
        )
        if not threats:
            return False

        nearby_friendly = (
            self.ai.units.closer_than(radius, nexus)
            | self.ai.structures.closer_than(radius, nexus)
        )
        return any(u.shield_health_percentage < 1.0 for u in nearby_friendly)

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
