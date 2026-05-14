from sc2.data import Race
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sharpy.plans import BuildOrder, Step, StepBuildGas
from sharpy.plans.acts import *
from sharpy.plans.acts.zerg import *
from sharpy.plans.require import *
from sharpy.plans.tactics.zerg import *

from montka.zerg.build import Build
from montka.zerg.common import zerg_tactics


def _plan() -> BuildOrder:
    expansions = [
        Step(None, Expand(2)),
        Step(UnitReady(UnitTypeId.SPAWNINGPOOL, 1), Expand(3)),
        Step(Supply(80), MorphLair()),
        Expand(4),
        Step(Supply(100), ActBuilding(UnitTypeId.EVOLUTIONCHAMBER, 2)),
    ]

    buildings = [
        Step(UnitExists(UnitTypeId.HATCHERY, 2, include_pending=True),
             ActBuilding(UnitTypeId.SPAWNINGPOOL, 1)),
        Step(UnitExists(UnitTypeId.QUEEN, 2), ActBuilding(UnitTypeId.ROACHWARREN, 1)),
    ]

    extractors = [
        StepBuildGas(1, UnitReady(UnitTypeId.SPAWNINGPOOL, 0.5)),
        StepBuildGas(2, UnitReady(UnitTypeId.ROACHWARREN, 1)),
        StepBuildGas(3, UnitExists(UnitTypeId.HATCHERY, 3)),
        StepBuildGas(4, UnitReady(UnitTypeId.HATCHERY, 3)),
    ]

    upgrades = [
        Step(UnitReady(UnitTypeId.LAIR, 1), None),
        Step(UnitExists(UnitTypeId.ROACHWARREN, 1), Tech(UpgradeId.GLIALRECONSTITUTION)),
        Step(UnitExists(UnitTypeId.EVOLUTIONCHAMBER, 1), Tech(UpgradeId.ZERGMISSILEWEAPONSLEVEL1)),
        Step(None, Tech(UpgradeId.ZERGGROUNDARMORSLEVEL1)),
        Step(None, Tech(UpgradeId.ZERGMISSILEWEAPONSLEVEL2)),
        Step(None, Tech(UpgradeId.ZERGGROUNDARMORSLEVEL2)),
    ]

    early_defense = [
        Step(UnitExists(UnitTypeId.SPAWNINGPOOL, 1),
             ActUnit(UnitTypeId.QUEEN, UnitTypeId.HATCHERY, 2)),
        Step(UnitExists(UnitTypeId.HATCHERY, 2),
             ActUnitOnce(UnitTypeId.ZERGLING, UnitTypeId.LARVA, 6)),
        Step(UnitExists(UnitTypeId.HATCHERY, 2, include_pending=True),
             ActUnit(UnitTypeId.QUEEN, UnitTypeId.HATCHERY, 3)),
        Step(UnitExists(UnitTypeId.HATCHERY, 3, include_pending=True),
             ActUnit(UnitTypeId.QUEEN, UnitTypeId.HATCHERY, 4)),
    ]

    army = [
        Step(UnitExists(UnitTypeId.HATCHERY, 2),
             ActUnit(UnitTypeId.ROACH, UnitTypeId.LARVA, 4)),
        Step(None, ActUnit(UnitTypeId.ZERGLING, UnitTypeId.LARVA, 4)),
        Step(UnitExists(UnitTypeId.HATCHERY, 3, include_pending=True),
             ActUnit(UnitTypeId.ROACH, UnitTypeId.LARVA)),
    ]

    ravagers = [
        Step(UnitReady(UnitTypeId.ROACH, 4), None),
        Step(UnitReady(UnitTypeId.ROACHWARREN, 1), MorphRavager(5), skip_until=Gas(200)),
        Step(UnitReady(UnitTypeId.ROACH, 10), MorphRavager(50), skip_until=Gas(300)),
    ]

    build = BuildOrder(
        ZergUnit(UnitTypeId.DRONE, 70),
        AutoOverLord(),
        expansions,
        buildings,
        extractors,
        early_defense,
        upgrades,
        ravagers,
        army,
    )

    return BuildOrder(build, zerg_tactics(attack_supply=120))


build = Build(
    name="roach",
    fn=_plan,
    weight=3,
    good_against=[Race.Terran, Race.Protoss],
    tags=["economic", "roach"],
)
