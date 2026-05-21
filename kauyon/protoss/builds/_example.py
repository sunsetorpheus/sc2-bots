# Example build file — reference template for creating new builds.
# Copy this file, rename it, and override only the values you want to change.
# All keys are optional; any key not set here falls back to the default in common.py.
#
# To activate a build, add it to the BUILDS list in builds/__init__.py.

from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId

# --- Overridable config keys ---
#
# "opener" (list[tuple[UnitTypeId, int]])
#   The opening structure sequence. Each entry is (UnitTypeId, count) — the opener
#   waits until that many of the structure exist before moving to the next step.
#   Use UnitTypeId.NEXUS as a sentinel to trigger a natural expansion at that point.
#   Default: DEFAULT_OPENER from common.py
#     Pylon×1 → Gateway×1 → Assimilator×1 → Nexus×2 → CyberneticsCore×1 → Assimilator×2
#   Example use: swap in a different sequence for an unconventional opening.
#
# "probe_max" (int)
#   Global probe cap for the entire game. Production stops when this count is
#   reached and resumes if probes are lost.
#   Default: PROBE_MAX from common.py (75)
#   Example use: set lower for an aggressive build that sacrifices economy for speed.
#
# "gas_total" (int)
#   Flat cap on total assimilators across all bases. Overrides the default
#   dynamic calculation (2 per qualifying base).
#   Default: not set — gas scales automatically with base count
#   Example use: 2-base timing push that wants exactly 3 gas instead of 4.
#
# "expand_at_harvesters" (int)
#   Mineral harvester count on a base that triggers both the next expansion and
#   gas construction at that base. Same threshold controls both for consistency.
#   Default: EXPAND_AT_HARVESTERS from common.py (14)
#   Example use: set lower for faster expanding, higher for slower greedy play.
#
# "expand_max" (int)
#   Hard cap on total bases regardless of saturation.
#   Default: EXPAND_MAX from common.py (8)
#   Example use: set to 2 for a 2-base all-in that never expands further.
#
# "build_steps" (dict[int, list[tuple[UnitTypeId, int]]])
#   Structures to build at each committed base count. Keys are base counts;
#   values are lists of (UnitTypeId, count) targets to reach by that base count.
#   All entries for lower base counts are also applied — they accumulate.
#   Default: BUILD_STEPS from common.py ({1: [(GATEWAY, 1)], 2: [(GATEWAY, 2)]})
#   Example use: add Forge + Twilight at 3 bases:
#     {1: [(GATEWAY, 1)], 2: [(GATEWAY, 2)], 3: [(FORGE, 1), (TWILIGHTCOUNCIL, 1)]}
#
# "gateway_max" (int)
#   Hard cap on total Gateways regardless of base count.
#   Default: GATEWAY_MAX from common.py (16)
#   Example use: cap at 8 for a 2-base all-in that doesn't need more gates.
#
# "chrono_energy_threshold" (int)
#   Minimum Nexus energy before firing Chrono Boost. Holding higher avoids
#   wasting energy on a nearly-finished job.
#   Default: CHRONO_ENERGY_THRESHOLD from common.py (75)
#   Example use: set lower (50) to chrono more aggressively in an early push.
#
# "defense_radius" (int)
#   Radius around a Nexus to check for friendly units/structures under attack.
#   Default: DEFENSE_RADIUS from common.py (20)
#
# "max_cannons_per_base" (int)
#   Maximum Photon Cannons per base when under attack. Requires a Forge.
#   Default: MAX_CANNONS_PER_BASE from common.py (2)
#
# "max_batteries_per_base" (int)
#   Maximum Shield Batteries per base when under attack. Requires a Gateway.
#   Default: MAX_BATTERIES_PER_BASE from common.py (1)
#
# "attack_supply" (int)
#   Army supply threshold that triggers the attack push. Bot rallies until this
#   is reached, then moves out.
#   Default: ATTACK_SUPPLY from common.py (100)
#   Example use: set lower for an early timing push, higher for a deathball style.
#
# "retreat_ratio" (float)
#   Fraction of attack_supply below which the army retreats home to rebuild.
#   Default: RETREAT_RATIO from common.py (0.3)
#   Example use: 0.5 to retreat earlier, 0.1 to fight to the last unit.
#
# "upgrades" (list[UpgradeId])
#   Extra upgrades to research on top of the defaults (weapons 1-2-3, armor 1-2-3).
#   Appended after the default list so defaults always research first.
#   Default: [] — no extras
#   Example use: add Blink for a Stalker build (requires Twilight Council).
#
# "army_comp" (dict)
#   Unit composition controlling all unit production. Two modes per unit type:
#
#   Proportion mode — relative share of the army, handled by SpawnController.
#     UnitTypeId.STALKER: {"proportion": 1.0, "priority": 2}
#     All proportion values must sum to 1.0.
#
#   Fixed-count mode — always maintain exactly this many, built first before proportions.
#     UnitTypeId.OBSERVER: {"count": 1, "priority": 0}
#     UnitTypeId.SENTRY:   {"count": 2, "priority": 1}
#     Handled by _spawn_fixed_count in production.py — excluded from SpawnController.
#
#   Both modes respect "priority" (lower = built first). Fixed-count units always
#   run before proportion units regardless of priority value.
#   Required for unit production — if not set, gates sit idle.
#
# (More keys will be documented here as steps are implemented.)

CONFIG = {
    # "expand_at_harvesters": 14,    # example: expand when base hits 14 mineral workers
    # "expand_max": 2,               # example: 2-base all-in, never expands further
    # "opener": [(UnitTypeId.PYLON, 1), (UnitTypeId.GATEWAY, 1), (UnitTypeId.CYBERNETICSCORE, 1)],
    # "probe_max": 44,  # example: rush build caps probes early to push faster
    # "gas_total": 3,               # example: 2-base timing push with main x2 + natural x1
    # "chrono_energy_threshold": 50, # example: chrono more aggressively in an early push
    # "build_steps": {1: [(UnitTypeId.GATEWAY, 1)], 2: [(UnitTypeId.GATEWAY, 2)], 3: [(UnitTypeId.FORGE, 1)]},
    # "gateway_max": 8,              # example: cap gates for a 2-base all-in
    # "attack_supply": 60,           # example: early timing push at lower supply
    # "upgrades": [UpgradeId.BLINKTECH],  # example: add Blink for a Stalker build
    # "army_comp": {
    #     UnitTypeId.STALKER: {"proportion": 1.0, "priority": 0},
    # },
}
