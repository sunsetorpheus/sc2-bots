from sharpy.plans import Step
from sharpy.plans.acts import *
from sharpy.plans.require import *
from sharpy.plans.tactics import *
from sharpy.plans.tactics.zerg import *


def zerg_tactics(attack_supply: int = 120):
    # Shared tactics applied every game step; order matters (defense checked before attack).
    return [
        MineOpenBlockedBase(),
        PlanCancelBuilding(),
        # Creep improves movement speed for zerg ground units.
        SpreadCreep(),
        # Queen larva inject is the primary production multiplier for Zerg.
        InjectLarva(),
        DistributeWorkers(),
        # Skip the first few frames to avoid conflicts during game initialization.
        Step(None, SpeedMining(), lambda ai: ai.client.game_step > 5),
        PlanZoneDefense(),
        PlanZoneGather(),
        PlanZoneAttack(attack_supply),
        PlanFinishEnemy(),
    ]
