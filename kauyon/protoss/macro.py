from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.ids.unit_typeid import UnitTypeId

from ares.behaviors.macro import AutoSupply, BuildStructure, BuildWorkers, ExpansionController, GasBuildingController, MacroPlan, Mining

from kauyon.protoss.common import (
    CHRONO_ENERGY_THRESHOLD,
    DEFAULT_OPENER,
    EXPAND_AT_HARVESTERS,
    EXPAND_MAX,
    GATEWAY_MAX,
    GATEWAY_PER_BASE,
    PROBE_MAX,
)


class Macro:
    def __init__(self, ai, config: dict):
        self.ai = ai
        self.config = config

    def add_behaviors(self, macro: MacroPlan) -> None:
        # Add all mineral-spending macro behaviors to the shared MacroPlan in
        # priority order. Called by plan.py before registering the plan.
        # Expansion is first so it can save for a Nexus before gates or units drain the bank.
        self._expansion(macro)
        self._opener(macro)
        self._gateways(macro)
        self._upgrade_structures(macro)
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

        # Always want at least 2 bases (main + natural).
        desired = 2

        # Only check expansions (not main) against the threshold — main is always
        # saturated once the natural is up, so including it would double-trigger.
        # Sort by distance from start so we evaluate bases in expansion order.
        home = self.ai.start_location
        expansions = sorted(
            [th for th in self.ai.townhalls.ready if th.distance_to(home) >= 10],
            key=lambda th: th.distance_to(home),
        )

        # Each saturated expansion triggers the next base.
        for th in expansions:
            if th.assigned_harvesters >= expand_at:
                desired += 1

        desired = min(desired, expand_max)
        macro.add(ExpansionController(to_count=desired, max_pending=1))

    def _opener(self, macro: MacroPlan) -> None:
        # Walk the opener sequence and queue the first structure that doesn't exist yet.
        # Stops after the first missing structure so buildings go up one at a time in order.
        # Build files can override "opener" in config to use a different sequence.
        opener: list = self.config.get("opener", DEFAULT_OPENER)

        for structure_id in opener:
            if not self.ai.structures(structure_id):
                kwargs = {"base_location": self.ai.start_location, "structure_id": structure_id}
                # first_pylon=True tells ares to use a special placement near the main ramp.
                if structure_id == UnitTypeId.PYLON and not self.ai.structures(UnitTypeId.PYLON):
                    kwargs["first_pylon"] = True
                macro.add(BuildStructure(**kwargs))
                return

    def _gateways(self, macro: MacroPlan) -> None:
        # Don't scale gates until every structure in the opener sequence exists.
        # This works regardless of what the opener ends with.
        opener: list = self.config.get("opener", DEFAULT_OPENER)
        if any(not self.ai.structures(s) for s in opener):
            return

        gateway_per_base = self.config.get("gateway_per_base", GATEWAY_PER_BASE)
        gateway_max = self.config.get("gateway_max", GATEWAY_MAX)

        # Count Gateways + Warpgates + pending together — once a Gateway morphs to
        # a Warpgate it disappears from GATEWAY, which would cause BuildStructure to
        # think fewer exist than the target and keep building indefinitely.
        total_gates = (
            len(self.ai.structures(UnitTypeId.GATEWAY))
            + len(self.ai.structures(UnitTypeId.WARPGATE))
            + self.ai.structure_pending(UnitTypeId.GATEWAY)
        )

        # Committed bases = ready Nexuses + any Nexus currently being built.
        bases_committed = (
            self.ai.townhalls.ready.amount
            + self.ai.structure_pending(self.ai.base_townhall_type)
        )

        # 2 gates on main, 4 on natural. Once 3rd base is committed, jump to
        # gateway_max — Kau'yon commits to full production from that point on.
        if bases_committed >= 3:
            target = gateway_max
        else:
            target = min(gateway_max, bases_committed * gateway_per_base)

        if total_gates < target:
            macro.add(BuildStructure(
                base_location=self.ai.start_location,
                structure_id=UnitTypeId.GATEWAY,
                to_count=target,
            ))

    def _upgrade_structures(self, macro: MacroPlan) -> None:
        # Build Forge and Twilight Council once 3rd base is committed.
        # Gated on 3rd base so minerals aren't bled before the economy is stable.
        bases_committed = (
            self.ai.townhalls.ready.amount
            + self.ai.structure_pending(self.ai.base_townhall_type)
        )
        if bases_committed < 3:
            return

        # Forge enables weapon and armor upgrades.
        if not self.ai.structures(UnitTypeId.FORGE):
            macro.add(BuildStructure(
                base_location=self.ai.start_location,
                structure_id=UnitTypeId.FORGE,
                to_count=1,
            ))

        # Twilight Council enables Blink research.
        if not self.ai.structures(UnitTypeId.TWILIGHTCOUNCIL):
            macro.add(BuildStructure(
                base_location=self.ai.start_location,
                structure_id=UnitTypeId.TWILIGHTCOUNCIL,
                to_count=1,
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

        # Priority: CyberCore researching > busy gates/warpgates > Nexus producing probes.
        # Chronoing the CyberCore speeds up Warpgate research which unlocks the whole army.
        cybers_busy = [
            s for s in self.ai.structures(UnitTypeId.CYBERNETICSCORE).ready
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

        targets = cybers_busy or gates_busy or nexus_busy
        if not targets:
            return

        # Each Nexus with enough energy chronos one target.
        for nexus in nexuses:
            if not targets:
                break
            nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, targets.pop(0))

    def _gas(self) -> None:
        # Don't build any gas until the Gateway is up — too early otherwise.
        if not self.ai.structures(UnitTypeId.GATEWAY):
            return

        # Build one assimilator early (before CyberCore is ready) to start
        # gas income flowing in time for Warpgate research.
        if not self.ai.structures(UnitTypeId.CYBERNETICSCORE):
            self.ai.register_behavior(GasBuildingController(to_count=1))
            return

        # If the build specifies a flat gas total, use that directly.
        if "gas_total" in self.config:
            self.ai.register_behavior(GasBuildingController(to_count=self.config["gas_total"]))
            return

        # Otherwise calculate dynamically: 2 assimilators per qualifying base.
        # Main base always qualifies. Expansions qualify once they hit the same
        # harvester threshold used for expansion — consistent saturation trigger.
        expand_at = self.config.get("expand_at_harvesters", EXPAND_AT_HARVESTERS)
        target = 0
        home = self.ai.start_location
        for th in self.ai.townhalls.ready:
            is_main = th.distance_to(home) < 10
            if is_main or th.assigned_harvesters >= expand_at:
                target += 2

        self.ai.register_behavior(GasBuildingController(to_count=target))

    def _mining(self) -> None:
        # Mining() is an ares behavior that handles all worker assignments:
        # - sends idle workers to the nearest mineral patch or gas
        # - rebalances workers returning from a finished structure build
        # - keeps workers spread across patches efficiently
        # It runs every step so no worker ever stays idle for long.
        self.ai.register_behavior(Mining())
