from sharpy.plans import BuildOrder, Step
from sharpy.plans.acts import *
from sharpy.plans.acts.terran import *
from sharpy.plans.require import *
from sharpy.plans.tactics import *
from sharpy.plans.tactics.terran import *
from sc2.ids.unit_typeid import UnitTypeId


def terran_scv():
    # Morph Orbitals as soon as Barracks is up; scale SCV cap with base count.
    return [
        Step(None, MorphOrbitals(), skip_until=UnitReady(UnitTypeId.BARRACKS, 1)),
        # Cap at 22 SCVs on the main until the natural is taken.
        Step(None, ActUnit(UnitTypeId.SCV, UnitTypeId.COMMANDCENTER, 22),
             skip=UnitExists(UnitTypeId.COMMANDCENTER, 2)),
        Step(None, ActUnit(UnitTypeId.SCV, UnitTypeId.COMMANDCENTER, 44)),
    ]


def terran_mule():
    # Call MULEs conservatively early game; dump energy aggressively after 5 minutes.
    return [
        Step(None, CallMule(50), skip=Time(5 * 60)),
        Step(None, CallMule(100), skip_until=Time(5 * 60)),
    ]


def terran_tactics(attack_supply: int = 26):
    # Shared tactics applied every game step; order matters (defense checked before attack).
    return [
        MineOpenBlockedBase(),
        PlanCancelBuilding(),
        # Lower Supply Depots when enemies approach so bio units can move through.
        LowerDepots(),
        PlanZoneDefense(),
        *terran_mule(),
        DistributeWorkers(),
        # Skip the first few frames to avoid conflicts during game initialization.
        Step(None, SpeedMining(), lambda ai: ai.client.game_step > 5),
        ManTheBunkers(),
        Repair(),
        ContinueBuilding(),
        PlanZoneGatherTerran(),
        PlanZoneAttack(attack_supply),
        PlanFinishEnemy(),
    ]
