from sharpy.plans import Step, StepBuildGas
from sharpy.plans.acts import *
from sharpy.plans.acts.protoss import *
from sharpy.plans.require import *
from sharpy.plans.require import RequireCustom
from sharpy.plans.tactics import *
from sc2.ids.unit_typeid import UnitTypeId

PROBE_MAX = 75
ATTACK_SUPPLY = 190

# Natural base has 14+ probes on minerals — safe to build both geysers.
_natural_saturated = RequireCustom(
    lambda ai: any(
        n.assigned_harvesters >= 14
        for n in ai.townhalls.ready
        if n.position != ai.start_location
    )
)

# Current bases are 80%+ saturated — time to expand to the next one.
_bases_saturated = RequireCustom(
    lambda ai: (
        sum(n.assigned_harvesters for n in ai.townhalls.ready) >=
        sum(n.ideal_harvesters for n in ai.townhalls.ready) * 0.8
    )
)


def _probe_production():
    return [
        ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, PROBE_MAX),
        ChronoUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS),
    ]


def _expansion():
    # Always expand when current bases are 80%+ saturated.
    # 75 probes naturally caps useful expansion at ~4 bases.
    return [
        Step(None, Expand(2), skip_until=_bases_saturated),
        Step(None, Expand(3), skip_until=_bases_saturated),
        Step(None, Expand(4), skip_until=_bases_saturated),
        Step(None, Expand(5), skip_until=_bases_saturated),
        Step(None, Expand(6), skip_until=_bases_saturated),
        Step(None, Expand(7), skip_until=_bases_saturated),
        Step(None, Expand(8), skip_until=_bases_saturated),
        Step(None, Expand(9), skip_until=_bases_saturated),
        Step(None, Expand(10), skip_until=_bases_saturated),
    ]


def protoss_gas():
    # Gas 1 and 2 are handled in the build order (opener sequence).
    # Natural: both geysers once 14+ probes are on minerals there.
    # 3rd base and beyond: both geysers immediately when the Nexus is ready.
    return [
        StepBuildGas(3, skip_until=_natural_saturated),
        StepBuildGas(4, skip_until=_natural_saturated),
        StepBuildGas(5, UnitReady(UnitTypeId.NEXUS, 3)),
        StepBuildGas(6, UnitReady(UnitTypeId.NEXUS, 3)),
        StepBuildGas(7, UnitReady(UnitTypeId.NEXUS, 4)),
        StepBuildGas(8, UnitReady(UnitTypeId.NEXUS, 4)),
    ]


def _economy():
    return [
        MineOpenBlockedBase(),
        DistributeWorkers(),
        Step(None, SpeedMining(), lambda ai: ai.client.game_step > 5),
    ]


def _defense():
    return [
        PlanCancelBuilding(),
        PlanZoneDefense(),
        RestorePower(),
    ]


def _attack(attack_supply: int = ATTACK_SUPPLY):
    return [
        PlanZoneGather(),
        # Attack only at max supply; after retreat hold in base until max supply again.
        Step(Supply(attack_supply), PlanZoneAttack(attack_supply)),
        PlanFinishEnemy(),
    ]


def protoss_tactics(attack_supply: int = ATTACK_SUPPLY):
    return [
        *_probe_production(),
        *_expansion(),
        *protoss_gas(),
        *_economy(),
        *_defense(),
        *_attack(attack_supply),
    ]
