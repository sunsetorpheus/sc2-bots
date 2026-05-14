from sharpy.plans import Step
from sharpy.plans.acts import *
from sharpy.plans.require import *
from sharpy.plans.tactics import *
from sharpy.plans.tactics.zerg import *


def zerg_tactics(attack_supply: int = 120):
    return [
        MineOpenBlockedBase(),
        PlanCancelBuilding(),
        SpreadCreep(),
        InjectLarva(),
        DistributeWorkers(),
        Step(None, SpeedMining(), lambda ai: ai.client.game_step > 5),
        PlanZoneDefense(),
        PlanZoneGather(),
        PlanZoneAttack(attack_supply),
        PlanFinishEnemy(),
    ]
