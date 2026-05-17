# ---------------------------------------------------------------------------
# Default macro parameters — the "Kauyon playstyle". Individual build configs
# can override any of these by including the matching key in their _config()
# dict. Keys not set in the build fall back to these defaults.
# ---------------------------------------------------------------------------

from sc2.ids.unit_typeid import UnitTypeId

# Opening structure sequence. Each entry is built once (in order); the next
# step only starts after the previous structure exists or is pending. Once
# every structure in the list is present, the engine takes over with normal
# gateway scaling and upgrade-structure logic. Default opener is the
# standard macro Protoss: Pylon → Gateway → Cybernetics Core.
OPENERS: list = [
    UnitTypeId.PYLON,
    UnitTypeId.GATEWAY,
    UnitTypeId.CYBERNETICSCORE,
]

# Worker cap.
PROBE_MAX: int = 75

# Maximum number of bases (hard ceiling). In practice the saturation logic
# drives expansion; this is a safety cap.
EXPAND_MAX: int = 99

# Supply threshold for the first all-in attack wave.
ATTACK_SUPPLY: int = 100

# Gateway scaling: bases_ready * GATEWAY_PER_BASE, capped at GATEWAY_MAX.
GATEWAY_PER_BASE: int = 4
GATEWAY_MAX: int = 16

# Chrono boost energy threshold — only use chrono when Nexus has this much energy.
CHRONO_ENERGY_THRESHOLD: float = 50.0

# Expansion trigger: bump desired base count when any ready Nexus has at
# least this many assigned harvesters. Lower = greedier expansion.
EXPAND_AT_HARVESTERS: int = 14

# Gas pickup at non-main bases: only build assimilators once the base has
# at least this many assigned harvesters. Lower = earlier gas, more Stalker
# production but slower base saturation.
GAS_AT_HARVESTERS: int = 4

# Gateway count cap before the 3rd Nexus completes. Holding gates low here
# preserves minerals for the Nexus and early upgrades.
PRE_THIRD_GATEWAY_CAP: int = 3

# Maximum Nexuses building at once. 1 is safe; 2 allows double-expansion on
# safe maps for macro builds.
MAX_PENDING_NEXUS: int = 1

# When saving for a Nexus, halt the MacroPlan (block army/structure spending)
# only while minerals are below this value. Above it, the Nexus has its 400
# already and army production can run alongside the save-up.
EXPAND_SAVE_MINERALS: int = 525

# Mid-attack retreat: abort the push when army_supply drops below
# ATTACK_SUPPLY * this ratio. 0.10 = retreat at 10%, 0.0 = never retreat.
ATTACK_ABORT_SUPPLY_RATIO: float = 0.30

# Mid-attack retreat: abort the push when this many enemy units are near a
# townhall. 999 effectively disables the rule (commit-to-push builds).
ATTACK_ABORT_ENEMY_COUNT: int = 5

# ---------------------------------------------------------------------------
# Micro defaults (read by per-unit modules in kauyon.protoss.micro).
# ---------------------------------------------------------------------------

# Stalker Blink retreat: trigger Blink to the nearest safe spot when a
# Stalker's combined HP+shield ratio drops below this AND the position is
# unsafe AND Blink is off cooldown. 0.0 disables the behavior. Has no
# effect until the build researches BlinkTech.
BLINK_RETREAT_HEALTH_PCT: float = 0.5

# ---------------------------------------------------------------------------
# Emergency worker defense (early-rush response).
# ---------------------------------------------------------------------------

# Pull probes to defend when threats reach a base and our army within 30
# of that base is outnumbered. Number pulled = threat_count *
# WORKER_DEFENSE_PER_THREAT, capped at WORKER_DEFENSE_MAX. Probes go back
# to mining when no threats remain near the base.
# Set WORKER_DEFENSE_MAX to 0 to disable.
WORKER_DEFENSE_PER_THREAT: int = 2
WORKER_DEFENSE_MAX: int = 8
