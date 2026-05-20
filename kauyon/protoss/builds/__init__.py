from dataclasses import dataclass, field
from typing import Callable, Any
from sc2.data import Race

from kauyon.protoss.builds.macro import macro_build
from kauyon.protoss.builds.stalker import stalker_build


@dataclass
class Build:
    name: str
    fn: Callable[[], Any]
    weight: int = 1
    good_against: list = field(default_factory=list)  # empty = all races
    tags: list = field(default_factory=list)


BUILDS = [
    # Default macro build — eligible against all races, picked most often.
    Build(name="macro", fn=macro_build, weight=1),
    # Stalker-focused build — only considered vs Terran, picked less often.
    Build(name="stalker", fn=stalker_build, weight=0, good_against=[Race.TERRAN]),
]
