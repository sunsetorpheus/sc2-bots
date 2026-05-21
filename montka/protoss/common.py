from sc2.ids.unit_typeid import UnitTypeId

# Maximum number of probes to maintain across all bases.
# Mont'ka caps early — 2-base saturation only, no over-droning.
PROBE_MAX = 44

# Harvester count on a base that triggers the next expansion.
EXPAND_AT_HARVESTERS = 16

# Hard cap on total bases. Mont'ka stays on 2 bases and attacks.
EXPAND_MAX = 2

# Radius around a Nexus to check for friendly units/structures under attack.
DEFENSE_RADIUS = 20

# Maximum Photon Cannons to build per base when under attack. Requires a Forge.
MAX_CANNONS_PER_BASE = 2

# Maximum Shield Batteries to build per base when under attack. Requires a Gateway.
MAX_BATTERIES_PER_BASE = 1

# Army supply threshold to trigger an attack push.
# Mont'ka attacks early with a smaller army than Kau'yon.
ATTACK_SUPPLY = 50

# Fraction of attack supply below which the army retreats home.
# Higher than Kau'yon — Mont'ka commits harder and retreats less.
RETREAT_RATIO = 0.1

# Structures to build at each committed base count.
# Mont'ka skips Forge/Twilight in defaults — just gates for fast pressure.
BUILD_STEPS = {
    1: [(UnitTypeId.GATEWAY, 1)],
    2: [(UnitTypeId.GATEWAY, 4)],
}

# Hard cap on total Gateways. Mont'ka caps lower for a tighter army.
GATEWAY_MAX = 6

# Minimum Nexus energy before firing Chrono Boost.
CHRONO_ENERGY_THRESHOLD = 50

# Default opener: no natural expand — straight 2-gate pressure.
# CyberCore comes right after first gate with no expand sentinel.
DEFAULT_OPENER = [
    (UnitTypeId.PYLON, 1),              # supply first
    (UnitTypeId.GATEWAY, 1),            # first gate immediately
    (UnitTypeId.ASSIMILATOR, 1),        # first gas
    (UnitTypeId.CYBERNETICSCORE, 1),    # unlock Stalkers and Warpgate research
    (UnitTypeId.ASSIMILATOR, 2),        # second gas
    (UnitTypeId.NEXUS, 2),              # natural — taken after pressure is already out
]
