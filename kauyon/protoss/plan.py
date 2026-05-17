import random
from sc2.constants import WORKER_TYPES
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

from kauyon.protoss.builds import BUILDS
from kauyon.protoss.micro import MICRO
from kauyon.protoss.common import (
    ATTACK_ABORT_ENEMY_COUNT,
    ATTACK_ABORT_SUPPLY_RATIO,
    ATTACK_SUPPLY,
    CHRONO_ENERGY_THRESHOLD,
    EXPAND_AT_HARVESTERS,
    EXPAND_MAX,
    EXPAND_SAVE_MINERALS,
    GAS_AT_HARVESTERS,
    GATEWAY_MAX,
    GATEWAY_PER_BASE,
    MAX_PENDING_NEXUS,
    OPENERS,
    PRE_THIRD_GATEWAY_CAP,
    PROBE_MAX,
    WORKER_DEFENSE_MAX,
    WORKER_DEFENSE_PER_THREAT,
)


class ProtossPlan:
    def __init__(self, ai, enemy_race: Race):
        self.ai = ai
        self.enemy_race = enemy_race
        self._config: dict = {}
        self._attacking: bool = False
        # Probes currently pulled for emergency defense. They're released
        # back to mining when no threats remain near any base.
        self._defender_tags: set[int] = set()

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
        gateway_per_base: int = cfg.get("gateway_per_base", GATEWAY_PER_BASE)
        gateway_max: int = cfg.get("gateway_max", GATEWAY_MAX)
        probe_max: int = cfg.get("probe_max", PROBE_MAX)
        attack_supply: int = cfg.get("attack_supply", ATTACK_SUPPLY)
        expand_max: int = cfg.get("expand_max", EXPAND_MAX)
        expand_at_harvesters: int = cfg.get("expand_at_harvesters", EXPAND_AT_HARVESTERS)
        gas_at_harvesters: int = cfg.get("gas_at_harvesters", GAS_AT_HARVESTERS)
        pre_third_gateway_cap: int = cfg.get("pre_third_gateway_cap", PRE_THIRD_GATEWAY_CAP)
        max_pending_nexus: int = cfg.get("max_pending_nexus", MAX_PENDING_NEXUS)
        expand_save_minerals: int = cfg.get("expand_save_minerals", EXPAND_SAVE_MINERALS)
        attack_abort_supply_ratio: float = cfg.get("attack_abort_supply_ratio", ATTACK_ABORT_SUPPLY_RATIO)
        attack_abort_enemy_count: int = cfg.get("attack_abort_enemy_count", ATTACK_ABORT_ENEMY_COUNT)
        openers: list = cfg.get("openers", OPENERS)
        worker_defense_per_threat: int = cfg.get("worker_defense_per_threat", WORKER_DEFENSE_PER_THREAT)
        worker_defense_max: int = cfg.get("worker_defense_max", WORKER_DEFENSE_MAX)

        expand_to = self._desired_base_count(expand_max, probe_max, expand_at_harvesters)
        # Cap probes to what current bases can actually use.
        effective_probe_cap = self._effective_probe_cap(probe_max)

        # Are we actively trying to expand? If so, ExpansionController must
        # *prioritize* (return True even when unaffordable) so the MacroPlan
        # halts and nothing below it spends the bank before the Nexus.
        # But only force-halt when we're close to affording — above
        # nexus_cost + stalker_cost (525) there's room for both, so let
        # army production continue. This keeps gates busy through the
        # save-up phase instead of idling for ~20s every expansion.
        bases_committed = ai.townhalls.ready.amount + ai.structure_pending(ai.base_townhall_type)
        wants_to_expand = bases_committed < expand_to
        prioritize_expand = wants_to_expand and ai.minerals < expand_save_minerals

        # -------------------------------------------------------------------
        # MacroPlan — ordered waterfall.
        # Expansion first, then probes (so Nexuses keep cranking workers while
        # the next base is in transit), then supply, then structures/army.
        # -------------------------------------------------------------------
        macro = MacroPlan()

        # 1. Expansion — highest priority so minerals aren't bled by gates first.
        # prioritize gated on bank size: only halt the MacroPlan when minerals
        # are close to (but not yet at) the Nexus cost. Above the threshold,
        # army can produce alongside the save-up without delaying the Nexus.
        macro.add(ExpansionController(
            to_count=expand_to,
            max_pending=max_pending_nexus,
            prioritize=prioritize_expand,
        ))

        # 2. Probes — kept ahead of structures so Nexuses don't stall while
        # gates spend the bank.
        macro.add(BuildWorkers(to_count=effective_probe_cap))

        # 3. Supply.
        macro.add(AutoSupply(base_location=ai.start_location))

        # 4. Structures (opener sequence → more Gateways → upgrade structures).
        self._add_structures(macro, gateway_per_base, gateway_max, upgrade_structures, expand_to, pre_third_gateway_cap, openers)

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
        ai.register_behavior(GasBuildingController(to_count=self._gas_target(gas_at_harvesters)))

        # Mining: returns idle/post-build workers to mineral lines.
        ai.register_behavior(Mining())

        # Chrono and attack logic.
        self._chrono_boost()
        self._run_micro()
        self._handle_worker_defense(worker_defense_per_threat, worker_defense_max)
        self._handle_attack(attack_supply, attack_abort_supply_ratio, attack_abort_enemy_count)

    # ---------------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------------

    def _desired_base_count(self, expand_max: int, probe_max: int, expand_at_harvesters: int) -> int:
        """
        Trigger expansion before bases are fully saturated so we have bank
        room to pay for the Nexus. Catches the base before ideal saturation
        (16 mineral + ~6 gas), giving the Nexus call time to land before
        gates/army drain the mineral pool.
        Always want at least 2 (main + natural).
        Counts pending Nexuses so desired keeps advancing while one is building.
        """
        ai = self.ai
        pending = ai.structure_pending(ai.base_townhall_type)
        desired = max(2, ai.townhalls.ready.amount + pending)

        for th in ai.townhalls.ready:
            if th.assigned_harvesters >= expand_at_harvesters:
                desired += 1

        max_for_probes = max(2, (probe_max // 16) + 1)
        return min(desired, expand_max, max_for_probes)

    def _effective_probe_cap(self, probe_max: int) -> int:
        """
        Cap probe production to the total ideal harvester count across all
        ready Nexuses plus gas slots. Pending bases (16 each) and pending
        assimilators (3 each) are also counted so Nexuses keep producing
        probes during the expansion's walk-time and warp-in, instead of
        idling until the new base finishes.
        """
        ai = self.ai
        total_ideal = sum(
            th.ideal_harvesters for th in ai.townhalls.ready
            if th.ideal_harvesters > 0
        )
        # Add gas slots (3 per ready assimilator).
        total_ideal += len(ai.gas_buildings.ready) * 3
        # Pre-allocate capacity for pending bases and gas so probe
        # production doesn't stall while expansions are in transit.
        total_ideal += ai.structure_pending(ai.base_townhall_type) * 16
        total_ideal += ai.structure_pending(UnitTypeId.ASSIMILATOR) * 3
        # Always allow at least 12 so early game isn't starved.
        return min(probe_max, max(12, total_ideal))

    def _gas_target(self, gas_at_harvesters: int) -> int:
        """
        2 assimilators per base. Main starts gas right after Gateway/Cyber.
        Non-main bases pick up gas once they reach gas_at_harvesters
        assigned workers — earlier means more Stalker gas but slower
        saturation; later means smoother expansion but gas-starved army.
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
            if is_main or th.assigned_harvesters >= gas_at_harvesters:
                target += 2
        return target

    def _add_structures(self, macro: MacroPlan, gateway_per_base: int, gateway_max: int, upgrade_structures: list, expand_to: int, pre_third_gateway_cap: int, openers: list) -> None:
        """
        Run the build's opener sequence, then scale Gateways with base
        count and queue upgrade structures. Uses BuildStructure's built-in
        to_count so ares handles the already-pending check correctly.

        Opener: walk the build's `openers` list in order. The next step
        only triggers once the previous structure exists (counting pending),
        so a build can express e.g. PYLON → FORGE → CANNON for a defensive
        opening or PYLON → GATEWAY → CYBER for a standard macro opening.
        While the opener isn't satisfied, no scaling/upgrade structures
        are queued — the opener is exclusive.

        While we want more bases than are ready+pending, hold back non-opener
        structures (extra gateways, upgrade structures) so minerals aren't
        bled while the Nexus probe walks. Once the Nexus is pending, the
        saving-for-base block lifts and gates/upgrades resume.
        """
        ai = self.ai

        # Walk the opener: find the first structure that isn't built or
        # pending, queue it, and stop. Pylon gets first_pylon=True so ares
        # places it at a sensible location relative to the main.
        for idx, struct_id in enumerate(openers):
            already_built = (
                len(ai.structures(struct_id))
                + ai.structure_pending(struct_id)
            ) > 0
            if not already_built:
                kwargs = {
                    "base_location": ai.start_location,
                    "structure_id": struct_id,
                }
                # First Pylon in the opener gets special placement.
                if struct_id == UnitTypeId.PYLON and idx == 0:
                    kwargs["first_pylon"] = True
                else:
                    kwargs["to_count"] = 1
                macro.add(BuildStructure(**kwargs))
                return

        bases_ready = ai.townhalls.ready.amount
        bases_committed = bases_ready + ai.structure_pending(ai.base_townhall_type)

        # Saving-for-Nexus gate: we want to expand and haven't started yet.
        # Skip gates/upgrade structures so the bank can pay for the Nexus.
        saving_for_base = bases_committed < expand_to

        if not saving_for_base:
            # Count gateways + warpgates together — once a gateway morphs to
            # a warpgate it disappears from GATEWAY, causing BuildStructure
            # to think fewer exist than the target and keep building.
            total_gates = (
                len(ai.structures(UnitTypeId.GATEWAY))
                + len(ai.structures(UnitTypeId.WARPGATE))
                + ai.structure_pending(UnitTypeId.GATEWAY)
            )

            # Scale gateways with READY base count, not committed — otherwise
            # the gate target jumps the moment a Nexus is placed and starts
            # eating minerals before the Nexus has even finished. Before the
            # 3rd Nexus completes, hold at pre_third_gateway_cap so the bank
            # isn't bled on gates that can't be fed.
            scaled_target = min(gateway_max, bases_ready * gateway_per_base)
            effective_gate_target = scaled_target if bases_ready >= 3 else min(pre_third_gateway_cap, scaled_target)

            if total_gates < effective_gate_target:
                macro.add(BuildStructure(
                    base_location=ai.start_location,
                    structure_id=UnitTypeId.GATEWAY,
                    to_count=effective_gate_target,
                ))

            # Upgrade structures (Forge, Twilight Council, etc.) — only once
            # the 3rd Nexus has finished, not just been placed.
            if bases_ready >= 3:
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

    # --- threat/chrono helpers -------------------------------------------

    @staticmethod
    def _is_threat(u: Unit) -> bool:
        """A unit counts as a threat if it's not a structure or resource."""
        return not u.is_structure and not u.is_mineral_field and not u.is_vespene_geyser

    def _threats_near_townhalls(self, radius: float = 30) -> Units:
        """Enemy non-resource units within `radius` of any of our townhalls."""
        ai = self.ai
        return ai.enemy_units.filter(
            lambda u: self._is_threat(u)
            and any(u.distance_to(th) < radius for th in ai.townhalls)
        )

    @staticmethod
    def _busy_unbuffed(structures) -> list[Unit]:
        """Structures with active orders that aren't already chrono-buffed."""
        return [s for s in structures if s.orders and not s.has_buff(BuffId.CHRONOBOOSTENERGYCOST)]

    def _recall(self, army: Units, home: Point2) -> None:
        """Abort the current push: flip state and order every unit home."""
        self._attacking = False
        for unit in army:
            unit.move(home)

    # --- micro dispatch --------------------------------------------------

    def _run_micro(self) -> None:
        """Dispatch each registered per-unit micro module to its units.

        Runs every frame, independent of the attack state machine — units
        should Blink/forcefield/etc. whether they're rallying, defending,
        or pushing.
        """
        ai = self.ai
        for module in MICRO:
            units: Units = ai.units(module.unit_types).ready
            if units:
                module.run(self, units)

    # --- chrono ----------------------------------------------------------

    def _chrono_boost(self) -> None:
        ai = self.ai

        nexuses_with_energy: list[Unit] = [
            nx for nx in ai.townhalls.ready
            if nx.energy >= CHRONO_ENERGY_THRESHOLD
            and not nx.has_buff(BuffId.CHRONOBOOSTENERGYCOST)
        ]
        if not nexuses_with_energy:
            return

        cybers_busy = self._busy_unbuffed(ai.structures(UnitTypeId.CYBERNETICSCORE).ready)
        gates_busy = self._busy_unbuffed(
            ai.structures(UnitTypeId.GATEWAY).ready | ai.structures(UnitTypeId.WARPGATE).ready
        )
        nexus_busy = self._busy_unbuffed(ai.townhalls.ready)

        targets: list[Unit] = cybers_busy or gates_busy or nexus_busy
        if not targets:
            return

        for nexus in nexuses_with_energy:
            if not targets:
                break
            target = targets.pop(0)
            nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, target)

    # --- worker defense (early rush response) ----------------------------

    def _handle_worker_defense(self, per_threat: int, max_defenders: int) -> None:
        """Pull probes to defend bases that are outnumbered by threats.

        Trigger: at least one threat is within 30 of a townhall AND our army
        within 30 of that townhall is fewer than the threats. Pull
        threat_count * per_threat probes (capped at max_defenders) to
        attack the nearest threat. Release probes back to mining once no
        threats remain near any base — Mining() picks them up automatically.
        """
        if max_defenders <= 0:
            return

        ai = self.ai
        army_types = set(self._config.get("army_comp", {}).keys())
        threats: Units = self._threats_near_townhalls()

        if not threats:
            # All clear — release any current defenders. Their attack
            # orders end naturally; clearing the tag set lets Mining()
            # take them back.
            self._defender_tags.clear()
            return

        # Pick the most-threatened base — the one with the most threats
        # within 30.
        most_threatened = max(
            ai.townhalls,
            key=lambda th: sum(1 for t in threats if t.distance_to(th) < 30),
        )
        local_threats = threats.filter(lambda t: t.distance_to(most_threatened) < 30)
        local_army = ai.units(army_types).ready.filter(
            lambda u: u.distance_to(most_threatened) < 30
        )

        # Army is sufficient — let the regular defense handler take it.
        if local_army.amount >= local_threats.amount:
            self._defender_tags.clear()
            return

        deficit = local_threats.amount - local_army.amount
        target_defender_count = min(deficit * per_threat, max_defenders)

        # Probes near the threatened base, sorted nearest-threat-first so we
        # pull the ones already in danger (they were going to die anyway).
        candidate_probes = ai.workers.filter(
            lambda w: w.distance_to(most_threatened) < 30
        )
        if not candidate_probes:
            return

        # Promote candidates up to target count.
        for probe in candidate_probes:
            if len(self._defender_tags) >= target_defender_count:
                break
            self._defender_tags.add(probe.tag)

        # Order all current defenders to attack the nearest threat.
        defenders = ai.workers.tags_in(self._defender_tags)
        for probe in defenders:
            target = local_threats.closest_to(probe)
            probe.attack(target)

    # --- attack state machine --------------------------------------------

    def _handle_attack(self, attack_supply: int, attack_abort_supply_ratio: float, attack_abort_enemy_count: int) -> None:
        ai = self.ai
        army_types = set(self._config.get("army_comp", {}).keys())
        if not army_types:
            return

        army: Units = ai.units(army_types).ready
        threats: Units = self._threats_near_townhalls()

        # Lone non-combat threats (1 worker, 1 zergling scout) don't justify
        # pulling the army. While attacking, require a substantive threat
        # (any combat unit OR 2+ units) before reacting. While rallying we
        # have time, so respond to anything.
        if threats and self._should_respond_to(threats):
            self._handle_defense(army, threats)
            return

        if self._attacking:
            self._handle_push(army, attack_supply, attack_abort_supply_ratio, attack_abort_enemy_count)
        else:
            self._handle_rally(army, attack_supply)

    def _should_respond_to(self, threats: Units) -> bool:
        if not self._attacking:
            return True  # While rallying, respond to anything.
        combat_threats = threats.filter(lambda u: u.can_attack and u.type_id not in WORKER_TYPES)
        return bool(combat_threats) or len(threats) >= 2

    def _handle_defense(self, army: Units, threats: Units) -> None:
        """Only units near a threat respond — forward attackers stay on target."""
        for unit in army:
            close_threats = threats.filter(lambda t: t.distance_to(unit) < 40)
            if close_threats:
                unit.attack(close_threats.closest_to(unit))

    def _handle_rally(self, army: Units, attack_supply: int) -> None:
        ai = self.ai
        if ai.supply_army >= attack_supply:
            self._attacking = True
            return

        # While rallying, fight any enemy units that are nearby rather than
        # ignoring them and continuing to move.
        rally: Point2 = self._rally_point(ai.start_location, ai.enemy_start_locations[0])
        for unit in army:
            close_enemies: Units = ai.enemy_units.filter(
                lambda u: self._is_threat(u) and u.distance_to(unit) < 15
            )
            if close_enemies:
                unit.attack(close_enemies.closest_to(unit))
            elif unit.distance_to(rally) > 5:
                unit.move(rally)

    def _handle_push(self, army: Units, attack_supply: int, attack_abort_supply_ratio: float, attack_abort_enemy_count: int) -> None:
        ai = self.ai
        home: Point2 = ai.start_location

        if ai.supply_army < attack_supply * attack_abort_supply_ratio:
            self._recall(army, home)
            return

        # Check for a serious threat at home while attacking — enough enemies
        # near any base means recall the whole army and reset the wave. Build
        # can disable this rule by setting the count very high (e.g. 999) for
        # commit-to-push playstyles.
        base_threats: Units = self._threats_near_townhalls()
        if len(base_threats) >= attack_abort_enemy_count:
            self._recall(army, home)
            return

        target: Point2 = self._attack_target()
        for unit in army:
            unit.attack(target)

    def _attack_target(self) -> Point2:
        """Pick where the army should push to.

        Priority:
          1. Closest known enemy structure to the average army position
             (handles the case where the enemy main is dead but expansions
             remain).
          2. Enemy starting location, if still unexplored.
          3. The next unexplored expansion location — sweeps the map to
             find what's left.
          4. Fall back to enemy_start_locations[0] as a last resort.
        """
        ai = self.ai

        if ai.enemy_structures:
            army_types = set(self._config.get("army_comp", {}).keys())
            army = ai.units(army_types).ready
            if army:
                ax = sum(u.position.x for u in army) / army.amount
                ay = sum(u.position.y for u in army) / army.amount
                anchor = Point2((ax, ay))
            else:
                anchor = ai.start_location
            return ai.enemy_structures.closest_to(anchor).position

        # No visible enemy structures — sweep unexplored expansions.
        for el in ai.expansion_locations_list:
            if not ai.is_visible(el):
                return el

        return ai.enemy_start_locations[0]
