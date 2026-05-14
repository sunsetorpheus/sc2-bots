from sharpy.plans import Step
from sharpy.plans.acts import *
from sharpy.plans.acts.protoss.restore_power import RestorePower
from sharpy.plans.require import *
from sharpy.plans.tactics import *
from sc2.ids.unit_typeid import UnitTypeId


def protoss_tactics(attack_gateways: int = 4):
    # Shared tactics applied every game step; order matters (defense checked before attack).
    return [
        MineOpenBlockedBase(),
        PlanZoneDefense(),
        # Re-powers buildings when a Pylon is destroyed mid-battle.
        RestorePower(),
        DistributeWorkers(),
        # Skip the first few frames to avoid conflicts during game initialization.
        Step(None, SpeedMining(), lambda ai: ai.client.game_step > 5),
        PlanZoneGather(),
        # Attack only once enough Gateways are ready to sustain warp-in pressure.
        Step(UnitReady(UnitTypeId.GATEWAY, attack_gateways), PlanZoneAttack(attack_gateways)),
        PlanFinishEnemy(),
    ]
