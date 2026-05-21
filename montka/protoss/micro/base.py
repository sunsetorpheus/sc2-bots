from typing import TYPE_CHECKING, Protocol, Set

from sc2.ids.unit_typeid import UnitTypeId
from sc2.units import Units

if TYPE_CHECKING:
    from montka.protoss.plan import ProtossPlan


class UnitMicro(Protocol):
    """Per-unit micro module.

    Implementations declare which unit types they handle via `unit_types`.
    Each frame, plan.on_step filters our army for matching units and calls
    `run(plan, units)`. The module is responsible for dispatching ability
    calls (Blink, Force Field, Snipe, etc.) on those units.

    Micro runs independently of the attack state machine — it fires whether
    the army is defending, rallying, or pushing. That matters for things
    like Blink-retreat, which should work in all three states.

    Why a Protocol: keeps each micro module a plain dataclass/class with no
    inheritance ceremony. As long as the two attributes exist, it works.
    """

    # Unit type ids this micro handles. plan.py filters the army to just
    # these before calling run().
    unit_types: Set[UnitTypeId]

    def run(self, plan: "ProtossPlan", units: Units) -> None:
        ...
