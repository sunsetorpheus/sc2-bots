from sharpy.plans import BuildOrder, Step
from sharpy.plans.acts import *
from sharpy.plans.acts.terran import *
from sharpy.plans.require import *
from sharpy.plans.tactics import *
from sharpy.plans.tactics.terran import *
from sc2.ids.unit_typeid import UnitTypeId


def terran_scv():
    return [
        Step(None, MorphOrbitals(), skip_until=UnitReady(UnitTypeId.BARRACKS, 1)),
        Step(None, ActUnit(UnitTypeId.SCV, UnitTypeId.COMMANDCENTER, 22),
             skip=UnitExists(UnitTypeId.COMMANDCENTER, 2)),
        Step(None, ActUnit(UnitTypeId.SCV, UnitTypeId.COMMANDCENTER, 44)),
    ]


def terran_mule():
    return [
        Step(None, CallMule(50), skip=Time(5 * 60)),
        Step(None, CallMule(100), skip_until=Time(5 * 60)),
    ]


def terran_tactics(attack_supply: int = 26):
    return [
        MineOpenBlockedBase(),
        PlanCancelBuilding(),
        LowerDepots(),
        PlanZoneDefense(),
        *terran_mule(),
        DistributeWorkers(),
        Step(None, SpeedMining(), lambda ai: ai.client.game_step > 5),
        ManTheBunkers(),
        Repair(),
        ContinueBuilding(),
        PlanZoneGatherTerran(),
        PlanZoneAttack(attack_supply),
        PlanFinishEnemy(),
    ]
