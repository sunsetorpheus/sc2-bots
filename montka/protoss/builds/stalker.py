from sc2.data import Race
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sharpy.plans import BuildOrder, Step, SequentialList, StepBuildGas
from sharpy.plans.acts import *
from sharpy.plans.acts.protoss import *
from sharpy.plans.require import *

from montka.protoss.build import Build
from montka.protoss.common import protoss_tactics


def _plan() -> BuildOrder:
    return BuildOrder(
        # Chrono Boost probes until 40 are out; only start once an Assimilator is up (gas needed for Stalkers).
        Step(
            None,
            ChronoUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS),
            skip=UnitExists(UnitTypeId.PROBE, 40, include_pending=True),
            skip_until=UnitExists(UnitTypeId.ASSIMILATOR, 1),
        ),
        # Sequential opener: probe saturation → Gateway → Cybernetics Core → natural expand.
        SequentialList(
            ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 14),
            GridBuilding(UnitTypeId.PYLON, 1),
            ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 16),
            BuildGas(1),
            GridBuilding(UnitTypeId.GATEWAY, 1),
            ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 20),
            Expand(2),
            # Cybernetics Core is required for Warp Gate research and Stalker production.
            GridBuilding(UnitTypeId.CYBERNETICSCORE, 1),
            ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 22),
            BuildGas(2),
            GridBuilding(UnitTypeId.PYLON, 2),
            BuildOrder(
                # AutoPylon automatically places pylons to prevent supply blocks.
                AutoPylon(),
                # Warp Gate converts Gateways for instant warp-ins at any pylon.
                Tech(UpgradeId.WARPGATERESEARCH),
                [
                    ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 22),
                    # Double the worker cap once the natural Nexus is established.
                    Step(UnitExists(UnitTypeId.NEXUS, 2), ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 44)),
                    # Third gas only when not already gas-rich.
                    StepBuildGas(3, skip=Gas(300)),
                ],
                [ProtossUnit(UnitTypeId.STALKER, 100)],
                # 7 gates provide enough warp-in cycles for sustained stalker production.
                [GridBuilding(UnitTypeId.GATEWAY, 7), StepBuildGas(4, skip=Gas(200))],
            ),
        ),
        # Attack once 4 Gateways are ready — enough warp-in cycles to sustain an aggressive push.
        protoss_tactics(attack_gateways=4),
    )


build = Build(
    name="stalker",
    fn=_plan,
    weight=3,
    good_against=[Race.Terran, Race.Zerg],
    tags=["bio", "gateway"],
)
