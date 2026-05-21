from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.ids.unit_typeid import UnitTypeId

from ares.behaviors.macro import AutoSupply, BuildStructure, BuildWorkers, GasBuildingController, MacroPlan, Mining

from kauyon.protoss.common import (
    BUILD_STEPS,
    CHRONO_ENERGY_THRESHOLD,
    DEFAULT_OPENER,
    EXPAND_AT_HARVESTERS,
    EXPAND_MAX,
    GATEWAY_MAX,
    PROBE_MAX,
)


class _ReserveForPendingNexus:
    """MacroPlan behavior that halts spending while a Nexus build is in-flight.

    Fixes a race in ares: ExpansionController (and our custom dispatch) dispatch
    a worker to walk to the expansion location, but minerals are only deducted
    when `worker.build()` fires at the target. During the walk, other MacroPlan
    behaviors (gates, probes, pylons) happily spend down the bank below 400, so
    when the worker arrives it sits idle until the 120s timeout cancels the
    build. By returning True (halting the MacroPlan waterfall) whenever a
    Nexus worker is en route AND we don't yet have 400 minerals, we starve the
    other behaviors so the bank only grows until the build fires.
    """

    def execute(self, ai, config, mediator) -> bool:
        # Cheap arithmetic check first — most frames either have enough
        # minerals or are nowhere near 400, so we never scan the tracker.
        if ai.minerals >= 400:
            return False
        nexus_type = ai.base_townhall_type
        return any(
            info.get("id") == nexus_type
            for info in mediator.get_building_tracker_dict.values()
        )


class Macro:
    def __init__(self, ai, config: dict):
        self.ai = ai
        self.config = config
        # Saturation latches: once a base crosses expand_at, it stays counted so
        # assigned_harvesters jitter at the boundary can't flap `desired`.
        self._saturated_tags: set[int] = set()
        # Reused across frames — the behavior is stateless, no need to allocate
        # a new instance every macro plan rebuild.
        self._reserve_nexus = _ReserveForPendingNexus()

    def add_behaviors(self, macro: MacroPlan) -> None:
        # Add all mineral-spending macro behaviors to the shared MacroPlan in
        # priority order. Called by plan.py before registering the plan.
        # The reservation behavior is added first: it halts the waterfall (returns
        # True) whenever a Nexus worker is en route and we're under 400 minerals,
        # preventing gates/probes/etc. from spending the bank below the Nexus cost
        # before the build worker can fire its `worker.build()` call.
        macro.add(self._reserve_nexus)
        self._expansion(macro)
        self._opener(macro)
        self._build_steps(macro)
        self._gateway_scaling(macro)
        self._supply(macro)
        self._build_workers(macro)

    def on_step(self) -> None:
        # Non-spending behaviors — run every step regardless of mineral budget.
        self._gas()
        self._chrono()
        self._mining()

    def _expansion(self, macro: MacroPlan) -> None:
        expand_at = self.config.get("expand_at_harvesters", EXPAND_AT_HARVESTERS)
        expand_max = self.config.get("expand_max", EXPAND_MAX)

        # Base desire is current committed base count — never shrink below what we have.
        # Each saturated non-main base adds 1 to signal readiness for the next expansion.
        nexus_type = self.ai.base_townhall_type
        ready_count = self.ai.townhalls.ready.amount
        pending_count = self.ai.structure_pending(nexus_type)
        desired = ready_count + pending_count

        home = self.ai.start_location
        saturated = self._saturated_tags

        # A single +1 signals "expand to the next base" — we never want more than
        # one step ahead. Stacking +1 per saturated base was causing desired to
        # jump multiple steps at once (e.g. 3→5 when two bases were already latched).
        any_saturated = False
        for th in self.ai.townhalls.ready:
            # Skip main — it's always saturated relative to expansions.
            if th.distance_to(home) < 10:
                continue

            if th.tag in saturated:
                any_saturated = True
            elif th.assigned_harvesters >= expand_at:
                saturated.add(th.tag)
                any_saturated = True

        if any_saturated:
            desired += 1

        if desired > expand_max:
            desired = expand_max

        self._dispatch_expansion(desired)

    def _dispatch_expansion(self, desired: int) -> None:
        # Custom expansion dispatch — replaces ares's ExpansionController to fix
        # a race: ExpansionController dispatches a far-away worker the moment
        # minerals first hit 400, but doesn't actually deduct minerals until the
        # worker arrives. The reservation behavior above complements this by
        # freezing other spending while the worker walks. Here we add force_close
        # worker selection (shorter walk) and a small mineral buffer to absorb
        # any frame-scale spending dips before the reservation kicks in.
        ai = self.ai

        # Cheap arithmetic checks first — most frames exit here.
        if ai.minerals < 450:
            return
        nexus_type = ai.base_townhall_type
        pending = ai.structure_pending(nexus_type)
        ready = ai.townhalls.ready.amount
        committed = ready + pending

        if pending >= 1 or committed >= desired:
            return

        # Find the next safe expansion location via the mediator. Expansions
        # come ranked by pathing distance from main. We must explicitly skip
        # locations where we already have a townhall — `location_is_blocked`
        # with default args doesn't consider own townhalls as blockers, so
        # without this filter the loop would re-pick our natural every frame.
        # The set of own townhall positions is built lazily on first miss so we
        # don't pay for it when the first candidate is already ours.
        mediator = ai.mediator
        own_th_positions: set[tuple[float, float]] | None = None
        location = None
        for el in mediator.get_own_expansions:
            candidate = el[0]
            cand_key = (round(candidate.x, 1), round(candidate.y, 1))
            if own_th_positions is None:
                own_th_positions = {
                    (round(th.position.x, 1), round(th.position.y, 1))
                    for th in ai.townhalls
                }
            if cand_key in own_th_positions:
                continue
            if ai.location_is_blocked(mediator, candidate):
                continue
            location = candidate
            break

        if location is None:
            return

        # force_close=True is the key fix — pick a worker near the target so the
        # walk window is short and minerals can't drain below 400 mid-walk.
        worker = mediator.select_worker(target_position=location, force_close=True)
        if worker is None:
            return

        mediator.build_with_specific_worker(
            worker=worker,
            structure_type=nexus_type,
            pos=location,
        )

    def _opener(self, macro: MacroPlan) -> None:
        # Walk the opener sequence and queue the first step not yet satisfied.
        # Each step is a (UnitTypeId, count) tuple — waits until that many exist.
        # NEXUS triggers _dispatch_expansion; ASSIMILATOR triggers GasBuildingController.
        # Stops after the first unsatisfied step so buildings go up one at a time.
        opener: list = self.config.get("opener", DEFAULT_OPENER)

        for structure_id, count in opener:
            existing = len(self.ai.structures(structure_id))
            if existing >= count:
                continue

            # NEXUS sentinel — delegate to the expansion dispatcher.
            if structure_id == UnitTypeId.NEXUS:
                self._dispatch_expansion(count)
                return

            # ASSIMILATOR — GasBuildingController handles gas placement, not BuildStructure.
            if structure_id == UnitTypeId.ASSIMILATOR:
                self.ai.register_behavior(GasBuildingController(to_count=count))
                return

            kwargs = {"base_location": self.ai.start_location, "structure_id": structure_id}
            # first_pylon=True tells ares to use special placement near the main ramp.
            if structure_id == UnitTypeId.PYLON and existing == 0:
                kwargs["first_pylon"] = True
            # to_count drives BuildStructure to the exact target for this step.
            kwargs["to_count"] = count
            macro.add(BuildStructure(**kwargs))
            return

    def _build_steps(self, macro: MacroPlan) -> None:
        # Don't build anything until the opener is complete.
        opener: list = self.config.get("opener", DEFAULT_OPENER)
        if any(len(self.ai.structures(s)) < count for s, count in opener):
            return

        gateway_max = self.config.get("gateway_max", GATEWAY_MAX)
        steps: dict = self.config.get("build_steps", BUILD_STEPS)

        bases_committed = (
            self.ai.townhalls.ready.amount
            + self.ai.structure_pending(self.ai.base_townhall_type)
        )

        # Collect all entries up to and including the current base count.
        # Higher base counts are ignored until we actually have those bases.
        targets: list[tuple] = []
        for base_count in sorted(steps):
            if base_count > bases_committed:
                break
            targets.extend(steps[base_count])

        # Queue the first unsatisfied structure.
        for structure_id, count in targets:
            # Gateways morph into Warpgates — count both to avoid over-building.
            if structure_id == UnitTypeId.GATEWAY:
                existing = (
                    len(self.ai.structures(UnitTypeId.GATEWAY))
                    + len(self.ai.structures(UnitTypeId.WARPGATE))
                    + self.ai.structure_pending(UnitTypeId.GATEWAY)
                )
                count = min(count, gateway_max)
            else:
                existing = len(self.ai.structures(structure_id))

            if existing < count:
                macro.add(BuildStructure(
                    base_location=self.ai.start_location,
                    structure_id=structure_id,
                    to_count=count if structure_id != UnitTypeId.GATEWAY else 0,
                ))
                return

    def _gateway_scaling(self, macro: MacroPlan) -> None:
        # After build steps are satisfied, keep adding gateways 2 at a time
        # but only when the mineral bank is 1000+ to avoid bleeding economy.
        if self.ai.minerals < 1000:
            return

        gateway_max = self.config.get("gateway_max", GATEWAY_MAX)
        total_gates = (
            len(self.ai.structures(UnitTypeId.GATEWAY))
            + len(self.ai.structures(UnitTypeId.WARPGATE))
            + self.ai.structure_pending(UnitTypeId.GATEWAY)
        )
        if total_gates >= gateway_max:
            return

        # Round up to the next even number so we always build in pairs.
        target = min(total_gates + 2, gateway_max)
        if total_gates < target:
            macro.add(BuildStructure(
                base_location=self.ai.start_location,
                structure_id=UnitTypeId.GATEWAY,
            ))

    def _supply(self, macro: MacroPlan) -> None:
        # AutoSupply() places Pylons before the bot hits the supply cap.
        # Ares handles timing and placement so the bot never supply blocks.
        macro.add(AutoSupply(base_location=self.ai.start_location))

    def _build_workers(self, macro: MacroPlan) -> None:
        # BuildWorkers() queues a Probe from every idle Nexus until the cap is reached.
        # If probes are lost, production resumes automatically until back at the cap.
        # Build files can override "probe_max" in config; falls back to the global default.
        probe_max = self.config.get("probe_max", PROBE_MAX)
        macro.add(BuildWorkers(to_count=probe_max))

    def _chrono(self) -> None:
        # Find Nexuses with enough energy that aren't already chronoed.
        threshold = self.config.get("chrono_energy_threshold", CHRONO_ENERGY_THRESHOLD)
        nexuses = [
            nx for nx in self.ai.townhalls.ready
            if nx.energy >= threshold
            and not nx.has_buff(BuffId.CHRONOBOOSTENERGYCOST)
        ]
        if not nexuses:
            return

        # Priority: CyberCore > Forge/Twilight researching > busy gates/warpgates > Nexus.
        # Chronoing the CyberCore speeds up Warpgate research which unlocks the whole army.
        cybers_busy = [
            s for s in self.ai.structures(UnitTypeId.CYBERNETICSCORE).ready
            if s.orders and not s.has_buff(BuffId.CHRONOBOOSTENERGYCOST)
        ]
        upgrade_structs_busy = [
            s for s in (
                self.ai.structures(UnitTypeId.FORGE).ready
                | self.ai.structures(UnitTypeId.TWILIGHTCOUNCIL).ready
            )
            if s.orders and not s.has_buff(BuffId.CHRONOBOOSTENERGYCOST)
        ]
        gates_busy = [
            s for s in (
                self.ai.structures(UnitTypeId.GATEWAY).ready
                | self.ai.structures(UnitTypeId.WARPGATE).ready
            )
            if s.orders and not s.has_buff(BuffId.CHRONOBOOSTENERGYCOST)
        ]
        nexus_busy = [
            nx for nx in self.ai.townhalls.ready
            if nx.orders and not nx.has_buff(BuffId.CHRONOBOOSTENERGYCOST)
        ]

        targets = cybers_busy or upgrade_structs_busy or gates_busy or nexus_busy
        if not targets:
            return

        # Each Nexus with enough energy chronos one target.
        for nexus in nexuses:
            if not targets:
                break
            nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, targets.pop(0))

    def _gas(self) -> None:
        # Gas in the opener (assimilators 1 and 2) is handled by _opener() via BuildStructure.
        # _gas() only runs the dynamic scaling logic once the CyberCore is ready.
        if not self.ai.structures(UnitTypeId.CYBERNETICSCORE).ready:
            return

        # If the build specifies a flat gas total, use that directly.
        if "gas_total" in self.config:
            self.ai.register_behavior(GasBuildingController(to_count=self.config["gas_total"]))
            return

        # Otherwise calculate dynamically: 2 assimilators per qualifying base.
        # Main always qualifies (early gas for Warpgate). Natural and onwards
        # qualify only once the *next* base's Nexus has been committed (ready or
        # pending) — i.e. gas goes up on base N when base N+1 starts building.
        # Bases are sorted nearest-to-home first so "next base" is unambiguous.
        home = self.ai.start_location
        nexus_type = self.ai.base_townhall_type
        committed_bases = self.ai.townhalls.ready.amount + self.ai.structure_pending(nexus_type)

        # Sort ready townhalls by distance from home: index 0 = main, index 1 = natural, etc.
        bases_sorted = sorted(self.ai.townhalls.ready, key=lambda th: th.distance_to(home))

        expand_max = self.config.get("expand_max", EXPAND_MAX)
        expand_at = self.config.get("expand_at_harvesters", EXPAND_AT_HARVESTERS)

        target = 0
        for i, th in enumerate(bases_sorted):
            is_main = i == 0
            # A non-main base qualifies once the next base (index i+1) is committed.
            # committed_bases counts ready + pending, so base i qualifies when committed > i+1.
            # Exception: if this is the last allowed base, qualify it once minerals saturate
            # so a base-capped bot still gets gas on its final expansion.
            is_last_base = (i + 1) == expand_max
            natural_saturated = is_last_base and th.assigned_harvesters >= expand_at
            qualified = is_main or committed_bases > i + 1 or natural_saturated
            if qualified:
                target += 2

        self.ai.register_behavior(GasBuildingController(to_count=target))

    def _mining(self) -> None:
        # Mining() is an ares behavior that handles all worker assignments:
        # - sends idle workers to the nearest mineral patch or gas
        # - rebalances workers returning from a finished structure build
        # - keeps workers spread across patches efficiently
        # It runs every step so no worker ever stays idle for long.
        self.ai.register_behavior(Mining())
