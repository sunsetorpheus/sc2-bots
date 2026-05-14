import random
from sc2.data import Race
from sharpy.plans import BuildOrder

from montka.protoss.builds import BUILDS


def protoss_plan(enemy_race: Race = None) -> BuildOrder:
    # Keep builds that counter the detected enemy race; empty good_against means the build works vs all races.
    candidates = [b for b in BUILDS if not b.good_against or enemy_race in b.good_against]

    # Fallback: if no build counters this matchup, use all builds.
    if not candidates:
        candidates = BUILDS

    # Weighted random pick — higher weight = more likely to be selected.
    weights = [b.weight for b in candidates]
    chosen = random.choices(candidates, weights=weights)[0]
    return chosen.fn()
