from sharpy.plans import Step
from sharpy.plans.acts import *
from sharpy.plans.require import *
from sharpy.plans.tactics import *
from sc2.ids.unit_typeid import UnitTypeId


def protoss_tactics(attack_gateways: int = 4):
    return [
        MineOpenBlockedBase(),
        PlanZoneDefense(),
        RestorePower(),
        DistributeWorkers(),
        Step(None, SpeedMining(), lambda ai: ai.client.game_step > 5),
        PlanZoneGather(),
        Step(UnitReady(UnitTypeId.GATEWAY, attack_gateways), PlanZoneAttack(attack_gateways)),
        PlanFinishEnemy(),
    ]
