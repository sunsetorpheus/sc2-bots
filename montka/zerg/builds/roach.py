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
    # Hatchery-first into 4-base economy; Lair unlocks Ravager morph and upgrade tiers.
    expansions = [
        Step(None, Expand(2)),
        Step(UnitReady(UnitTypeId.SPAWNINGPOOL, 1), Expand(3)),
        # Lair is required for Glial Reconstitution (Ravager speed upgrade).
        Step(Supply(80), MorphLair()),
        Expand(4),
        # Two chambers allow weapon and armor upgrades to research in parallel.
        Step(Supply(100), ActBuilding(UnitTypeId.EVOLUTIONCHAMBER, 2)),
    ]

    # Spawning Pool after the natural hatchery; Roach Warren after queens are up for defense.
    buildings = [
        Step(UnitExists(UnitTypeId.HATCHERY, 2, include_pending=True),
             ActBuilding(UnitTypeId.SPAWNINGPOOL, 1)),
        Step(UnitExists(UnitTypeId.QUEEN, 2), ActBuilding(UnitTypeId.ROACHWARREN, 1)),
    ]

    # Gas timing is staggered: early gas for roach production, more gas as the army scales.
    extractors = [
        StepBuildGas(1, UnitReady(UnitTypeId.SPAWNINGPOOL, 0.5)),
        StepBuildGas(2, UnitReady(UnitTypeId.ROACHWARREN, 1)),
        StepBuildGas(3, UnitExists(UnitTypeId.HATCHERY, 3)),
        StepBuildGas(4, UnitReady(UnitTypeId.HATCHERY, 3)),
    ]

    # Upgrades unlock in order: Glial (speed) → weapon 1 → armor 1 → weapon 2 → armor 2.
    upgrades = [
        # Gate step: Glial Reconstitution requires Lair to be complete.
        Step(UnitReady(UnitTypeId.LAIR, 1), None),
        Step(UnitExists(UnitTypeId.ROACHWARREN, 1), Tech(UpgradeId.GLIALRECONSTITUTION)),
        Step(UnitExists(UnitTypeId.EVOLUTIONCHAMBER, 1), Tech(UpgradeId.ZERGMISSILEWEAPONSLEVEL1)),
        Step(None, Tech(UpgradeId.ZERGGROUNDARMORSLEVEL1)),
        Step(None, Tech(UpgradeId.ZERGMISSILEWEAPONSLEVEL2)),
        Step(None, Tech(UpgradeId.ZERGGROUNDARMORSLEVEL2)),
    ]

    # Queens per hatchery for larva inject and anti-air; 6 zerglings as an early wall against rushes.
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

    # Keep 4 roaches and 4 zerglings at home early; flood roaches once the third base is up.
    army = [
        Step(UnitExists(UnitTypeId.HATCHERY, 2),
             ActUnit(UnitTypeId.ROACH, UnitTypeId.LARVA, 4)),
        Step(None, ActUnit(UnitTypeId.ZERGLING, UnitTypeId.LARVA, 4)),
        Step(UnitExists(UnitTypeId.HATCHERY, 3, include_pending=True),
             ActUnit(UnitTypeId.ROACH, UnitTypeId.LARVA)),
    ]

    # Morph Ravagers once a roach core is established; Bile makes siege lines and buildings vulnerable.
    ravagers = [
        # Wait for a roach core before spending gas on morphs.
        Step(UnitReady(UnitTypeId.ROACH, 4), None),
        Step(UnitReady(UnitTypeId.ROACHWARREN, 1), MorphRavager(5), skip_until=Gas(200)),
        Step(UnitReady(UnitTypeId.ROACH, 10), MorphRavager(50), skip_until=Gas(300)),
    ]

    build = BuildOrder(
        # Target 70 drones to saturate 4 bases (≈16-17 per base).
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

    # Attack at supply 120 — large enough roach/ravager army to break fortified positions.
    return BuildOrder(build, zerg_tactics(attack_supply=120))


build = Build(
    name="roach",
    fn=_plan,
    weight=3,
    good_against=[Race.Terran, Race.Protoss],
    tags=["economic", "roach"],
)
