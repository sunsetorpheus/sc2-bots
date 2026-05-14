from sc2.data import Race
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sharpy.plans import BuildOrder, Step, StepBuildGas
from sharpy.plans.acts import *
from sharpy.plans.acts.terran import *
from sharpy.plans.require import *
from sharpy.plans.tactics.terran import *

from montka.terran.build import Build
from montka.terran.common import terran_scv, terran_tactics


def _plan() -> BuildOrder:
    # Standard 1-1-1 reaper opener into bio expansion.
    opener = [
        Step(Supply(13), GridBuilding(UnitTypeId.SUPPLYDEPOT, 1, priority=True)),
        GridBuilding(UnitTypeId.BARRACKS, 1, priority=True),
        StepBuildGas(1, Supply(15)),
        # Scout/harass; triggers marine production once confirmed built.
        TerranUnit(UnitTypeId.REAPER, 1, only_once=True, priority=True),
        Expand(2),
        GridBuilding(UnitTypeId.SUPPLYDEPOT, 2, priority=True),
        BuildAddon(UnitTypeId.BARRACKSREACTOR, UnitTypeId.BARRACKS, 1),
        GridBuilding(UnitTypeId.FACTORY, 1),
        # Factory tech lab is required for Stimpack and Shield Wall research.
        BuildAddon(UnitTypeId.FACTORYTECHLAB, UnitTypeId.FACTORY, 1),
        AutoDepot(),
    ]

    # Scale up production and take a third base at supply 40.
    buildings = [
        Step(None, GridBuilding(UnitTypeId.BARRACKS, 2)),
        BuildGas(2),
        Step(None, BuildAddon(UnitTypeId.BARRACKSTECHLAB, UnitTypeId.BARRACKS, 1)),
        Step(None, GridBuilding(UnitTypeId.STARPORT, 1)),
        Step(None, GridBuilding(UnitTypeId.BARRACKS, 3)),
        Step(None, BuildAddon(UnitTypeId.BARRACKSTECHLAB, UnitTypeId.BARRACKS, 2)),
        Step(Supply(40), Expand(3)),
        Step(None, GridBuilding(UnitTypeId.BARRACKS, 5)),
        Step(None, BuildAddon(UnitTypeId.BARRACKSREACTOR, UnitTypeId.BARRACKS, 3)),
        Step(None, BuildAddon(UnitTypeId.STARPORTREACTOR, UnitTypeId.STARPORT, 1)),
        BuildGas(4),
    ]

    # Core bio upgrades: Concussive Shells, Stim, Combat Shield.
    tech = [
        Step(None, Tech(UpgradeId.PUNISHERGRENADES)),
        Step(None, Tech(UpgradeId.STIMPACK)),
        Step(None, Tech(UpgradeId.SHIELDWALL)),
    ]

    # Medivacs heal bio units in the field; prioritise up to 4.
    air = [
        Step(UnitReady(UnitTypeId.STARPORT, 1), TerranUnit(UnitTypeId.MEDIVAC, 2, priority=True)),
        Step(UnitReady(UnitTypeId.STARPORT, 1), TerranUnit(UnitTypeId.MEDIVAC, 4, priority=True)),
    ]

    # After the reaper is confirmed built, begin marine/marauder production.
    marines = [
        Step(UnitExists(UnitTypeId.REAPER, 1, include_killed=True), TerranUnit(UnitTypeId.MARINE, 2)),
        BuildOrder([
            TerranUnit(UnitTypeId.MARAUDER, 20, priority=True),
            TerranUnit(UnitTypeId.MARINE, 20),
            # Flood marines when minerals are high to avoid floating resources.
            Step(Minerals(250), TerranUnit(UnitTypeId.MARINE, 100)),
        ]),
    ]

    # Attack triggers at supply 26 — enough bio to pressure before full upgrades land.
    return BuildOrder([terran_scv(), opener, buildings, tech, air, marines, terran_tactics(attack_supply=26)])


build = Build(
    name="bio",
    fn=_plan,
    weight=3,
    good_against=[Race.Zerg, Race.Protoss],
    tags=["aggressive", "bio"],
)
