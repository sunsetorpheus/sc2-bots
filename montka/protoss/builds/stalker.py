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
        Step(
            None,
            ChronoUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS),
            skip=UnitExists(UnitTypeId.PROBE, 40, include_pending=True),
            skip_until=UnitExists(UnitTypeId.ASSIMILATOR, 1),
        ),
        SequentialList(
            ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 14),
            GridBuilding(UnitTypeId.PYLON, 1),
            ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 16),
            BuildGas(1),
            GridBuilding(UnitTypeId.GATEWAY, 1),
            ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 20),
            Expand(2),
            GridBuilding(UnitTypeId.CYBERNETICSCORE, 1),
            ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 22),
            BuildGas(2),
            GridBuilding(UnitTypeId.PYLON, 2),
            BuildOrder(
                AutoPylon(),
                Tech(UpgradeId.WARPGATERESEARCH),
                [
                    ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 22),
                    Step(UnitExists(UnitTypeId.NEXUS, 2), ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 44)),
                    StepBuildGas(3, skip=Gas(300)),
                ],
                [ProtossUnit(UnitTypeId.STALKER, 100)],
                [GridBuilding(UnitTypeId.GATEWAY, 7), StepBuildGas(4, skip=Gas(200))],
            ),
        ),
        protoss_tactics(attack_gateways=4),
    )


build = Build(
    name="stalker",
    fn=_plan,
    weight=3,
    good_against=[Race.Terran, Race.Zerg],
    tags=["bio", "gateway"],
)
