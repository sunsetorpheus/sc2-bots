import random
from sc2.data import Race
from sharpy.plans import BuildOrder

from montka.protoss.builds import BUILDS


def protoss_plan(enemy_race: Race = None) -> BuildOrder:
    candidates = [b for b in BUILDS if not b.good_against or enemy_race in b.good_against]

    if not candidates:
        candidates = BUILDS

    weights = [b.weight for b in candidates]
    chosen = random.choices(candidates, weights=weights)[0]
    return chosen.fn()
