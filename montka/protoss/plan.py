import random
from sc2.data import Race
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

from ares.behaviors.macro import (
    AutoSupply,
    BuildStructure,
    BuildWorkers,
    ExpansionController,
    GasBuildingController,
    MacroPlan,
    Mining,
    SpawnController,
    UpgradeController,
)

from montka.protoss.builds import BUILDS
from montka.protoss.common import (
    ATTACK_SUPPLY,
    CHRONO_ENERGY_THRESHOLD,
    EXPAND_MAX,
    PROBE_MAX,
)


class ProtossPlan:
    def __init__(self, ai, enemy_race: Race):
        self.ai = ai
        self.enemy_race = enemy_race
        self._config: dict = {}
        self._attacking: bool = False

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
        upgrade_structures: list = cfg.get("upgrade_structures", [])
        gateway_per_base: int = cfg.get("gateway_per_base", 4)
        gateway_max: int = cfg.get("gateway_max", 16)
        probe_max: int = cfg.get("probe_max", PROBE_MAX)
        attack_supply: int = cfg.get("attack_supply", ATTACK_SUPPLY)
        expand_max: int = cfg.get("expand_max", EXPAND_MAX)

        expand_to = self._desired_base_count(expand_max, probe_max)
        # Cap probes to what current bases can actually use.
        effective_probe_cap = self._effective_probe_cap(probe_max)

        # -------------------------------------------------------------------
        # MacroPlan — ordered waterfall.
        # Expansion is first so it can save for a Nexus before gates/units
        # drain the bank. Supply and probes follow, then structures and army.
        # -------------------------------------------------------------------
        macro = MacroPlan()

        # 1. Expansion — highest priority so minerals aren't bled by gates first.
        macro.add(ExpansionController(to_count=expand_to, max_pending=1))

        # 2. Supply.
        macro.add(AutoSupply(base_location=ai.start_location))

        # 3. Probes — only up to what current bases can absorb.
        macro.add(BuildWorkers(to_count=effective_probe_cap))

        # 4. Structures (Pylon → Gateway → CyberCore → more Gateways).
        self._add_structures(macro, gateway_per_base, gateway_max, upgrade_structures)

        # 5. Upgrades — auto_tech_up disabled so UpgradeController never builds
        # Forge/Twilight/etc. on its own; _add_structures handles those gated to 3rd base.
        if upgrades and ai.structures(UnitTypeId.CYBERNETICSCORE).ready:
            macro.add(
                UpgradeController(
                    upgrade_list=upgrades,
                    base_location=ai.start_location,
                    auto_tech_up_enabled=False,
                )
            )

        # 6. Army.
        if army_comp and ai.structures(UnitTypeId.GATEWAY).ready:
            macro.add(SpawnController(army_composition_dict=army_comp))

        ai.register_behavior(macro)

        # -------------------------------------------------------------------
        # Independent behaviors — not mineral-spending so safe to always run.
        # -------------------------------------------------------------------

        # Gas: gated by base readiness, runs regardless of MacroPlan result.
        ai.register_behavior(GasBuildingController(to_count=self._gas_target()))

        # Mining: returns idle/post-build workers to mineral lines.
        ai.register_behavior(Mining())

        # Chrono and attack logic.
        self._chrono_boost()
        self._handle_attack(attack_supply)

    # ---------------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------------

    def _desired_base_count(self, expand_max: int, probe_max: int) -> int:
        """
        Expand whenever any ready Nexus reports surplus_harvesters >= 0
        (assigned >= ideal), meaning the base is at capacity.
        Always want at least 2 (main + natural).
        Counts pending Nexuses so desired keeps advancing while one is building.
        """
        ai = self.ai
        pending = ai.structure_pending(ai.base_townhall_type)
        desired = max(2, ai.townhalls.ready.amount + pending)

        for th in ai.townhalls.ready:
            if th.surplus_harvesters >= 0:
                desired += 1

        max_for_probes = max(2, (probe_max // 16) + 1)
        return min(desired, expand_max, max_for_probes)

    def _effective_probe_cap(self, probe_max: int) -> int:
        """
        Cap probe production to the total ideal harvester count across all
        ready Nexuses plus gas slots, so we don't overproduce probes that
        have nowhere to go and waste minerals while saving for a Nexus.
        """
        ai = self.ai
        total_ideal = sum(
            th.ideal_harvesters for th in ai.townhalls.ready
            if th.ideal_harvesters > 0
        )
        # Add gas slots (3 per ready assimilator).
        total_ideal += len(ai.gas_buildings.ready) * 3
        # Always allow at least 12 so early game isn't starved.
        return min(probe_max, max(12, total_ideal))

    def _gas_target(self) -> int:
        """
        2 assimilators per base, but only once a non-main Nexus has 8+
        workers — avoids pulling probes off a fresh expansion too early.
        """
        ai = self.ai
        if not ai.structures(UnitTypeId.GATEWAY):
            return 0
        if not ai.structures(UnitTypeId.CYBERNETICSCORE):
            return 1

        target = 0
        home = ai.start_location
        for th in ai.townhalls.ready:
            is_main = th.distance_to(home) < 10
            if is_main or th.assigned_harvesters >= 8:
                target += 2
        return target

    def _add_structures(self, macro: MacroPlan, gateway_per_base: int, gateway_max: int, upgrade_structures: list) -> None:
        """
        Pylon → Gateway → CyberneticsCore → scale Gateways with base count.
        Uses BuildStructure's built-in to_count so ares handles the
        already-pending check correctly.
        """
        ai = self.ai

        if not ai.structures(UnitTypeId.PYLON):
            macro.add(BuildStructure(
                base_location=ai.start_location,
                structure_id=UnitTypeId.PYLON,
                first_pylon=True,
            ))
            return

        if not ai.structures(UnitTypeId.GATEWAY):
            macro.add(BuildStructure(
                base_location=ai.start_location,
                structure_id=UnitTypeId.GATEWAY,
                to_count=1,
            ))
            return

        if not ai.structures(UnitTypeId.CYBERNETICSCORE):
            macro.add(BuildStructure(
                base_location=ai.start_location,
                structure_id=UnitTypeId.CYBERNETICSCORE,
                to_count=1,
            ))
            return

        bases_committed = ai.townhalls.ready.amount + ai.structure_pending(ai.base_townhall_type)

        # Count gateways + warpgates together — once a gateway morphs to a
        # warpgate it disappears from GATEWAY, causing BuildStructure to
        # think fewer exist than the target and keep building indefinitely.
        total_gates = (
            len(ai.structures(UnitTypeId.GATEWAY))
            + len(ai.structures(UnitTypeId.WARPGATE))
            + ai.structure_pending(UnitTypeId.GATEWAY)
        )

        # Scale gateways with committed base count: gateway_per_base per base,
        # capped at gateway_max. Hold at 2 until 3rd base committed so minerals
        # aren't bled before the Nexus is started.
        scaled_target = min(gateway_max, bases_committed * gateway_per_base)
        effective_gate_target = scaled_target if bases_committed >= 3 else min(2, scaled_target)

        if total_gates < effective_gate_target:
            macro.add(BuildStructure(
                base_location=ai.start_location,
                structure_id=UnitTypeId.GATEWAY,
                to_count=effective_gate_target,
            ))

        # Upgrade structures (Forge, Twilight Council, etc.) — only after 3rd base.
        if bases_committed >= 3:
            for struct_id in upgrade_structures:
                if not ai.structures(struct_id):
                    macro.add(BuildStructure(
                        base_location=ai.start_location,
                        structure_id=struct_id,
                        to_count=1,
                    ))

        # Ensure each non-main expansion has at least 2 pylons nearby.
        for th in ai.townhalls.ready:
            if th.distance_to(ai.start_location) < 10:
                continue
            pylons_nearby = ai.structures(UnitTypeId.PYLON).closer_than(15, th)
            if len(pylons_nearby) < 2:
                macro.add(BuildStructure(
                    base_location=th.position,
                    structure_id=UnitTypeId.PYLON,
                ))

    def _rally_point(self, home: Point2, enemy_start: Point2) -> Point2:
        """
        Average position of the two furthest bases (ready or pending) from main,
        nudged toward the enemy. Includes building Nexuses so the rally point
        advances as soon as construction starts, not when it finishes.
        """
        ai = self.ai
        all_bases = list(ai.townhalls)  # ready + not ready (building)
        if not all_bases:
            return home.towards(enemy_start, 15)

        # Sort furthest-first, take up to two frontier bases.
        frontier = sorted(all_bases, key=lambda th: th.distance_to(home), reverse=True)[:2]
        cx = sum(th.position.x for th in frontier) / len(frontier)
        cy = sum(th.position.y for th in frontier) / len(frontier)
        return Point2((cx, cy)).towards(enemy_start, 8)

    def _chrono_boost(self) -> None:
        ai = self.ai

        nexuses_with_energy: list[Unit] = [
            nx for nx in ai.townhalls.ready
            if nx.energy >= CHRONO_ENERGY_THRESHOLD
            and not nx.has_buff(BuffId.CHRONOBOOSTENERGYCOST)
        ]
        if not nexuses_with_energy:
            return

        cybers_busy = [
            s for s in ai.structures(UnitTypeId.CYBERNETICSCORE).ready
            if s.orders and not s.has_buff(BuffId.CHRONOBOOSTENERGYCOST)
        ]
        gates_busy = [
            s for s in (
                ai.structures(UnitTypeId.GATEWAY).ready
                | ai.structures(UnitTypeId.WARPGATE).ready
            )
            if s.orders and not s.has_buff(BuffId.CHRONOBOOSTENERGYCOST)
        ]
        nexus_busy = [
            nx for nx in ai.townhalls.ready
            if nx.orders and not nx.has_buff(BuffId.CHRONOBOOSTENERGYCOST)
        ]

        targets: list[Unit] = cybers_busy or gates_busy or nexus_busy
        if not targets:
            return

        for nexus in nexuses_with_energy:
            if not targets:
                break
            target = targets.pop(0)
            nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, target)

    def _handle_attack(self, attack_supply: int) -> None:
        ai = self.ai
        army_types = set(self._config.get("army_comp", {}).keys())
        if not army_types:
            return

        army: Units = ai.units(army_types).ready
        army_supply: float = ai.supply_army
        enemy_start: Point2 = ai.enemy_start_locations[0]
        home: Point2 = ai.start_location

        # Any visible enemy non-structure near any of our bases is a threat.
        threats: Units = ai.enemy_units.filter(
            lambda u: not u.is_structure
            and not u.is_mineral_field
            and not u.is_vespene_geyser
            and any(u.distance_to(th) < 30 for th in ai.townhalls)
        )

        if threats:
            for unit in army:
                unit.attack(threats.closest_to(unit))
            return

        if not self._attacking:
            if army_supply >= attack_supply:
                self._attacking = True
            else:
                # While rallying, fight any enemy units that are nearby rather
                # than ignoring them and continuing to move.
                rally: Point2 = self._rally_point(home, enemy_start)
                for unit in army:
                    close_enemies: Units = ai.enemy_units.filter(
                        lambda u: not u.is_structure
                        and not u.is_mineral_field
                        and not u.is_vespene_geyser
                        and u.distance_to(unit) < 15
                    )
                    if close_enemies:
                        unit.attack(close_enemies.closest_to(unit))
                    elif unit.distance_to(rally) > 5:
                        unit.move(rally)
        else:
            if army_supply < attack_supply * 0.10:
                self._attacking = False
                for unit in army:
                    unit.move(home)
            else:
                # Check for a serious threat at home while attacking — 5+ enemy
                # units near any base means recall the whole army and reset the wave.
                base_threats: Units = ai.enemy_units.filter(
                    lambda u: not u.is_structure
                    and not u.is_mineral_field
                    and not u.is_vespene_geyser
                    and any(u.distance_to(th) < 30 for th in ai.townhalls)
                )
                if len(base_threats) >= 5:
                    self._attacking = False
                    for unit in army:
                        unit.move(home)
                else:
                    for unit in army:
                        unit.attack(enemy_start)
