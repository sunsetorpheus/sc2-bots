from dataclasses import dataclass, field
from typing import Callable, Any
from sc2.data import Race

from kauyon.protoss.builds.mass_stalker import mass_stalker_build


@dataclass
class Build:
    name: str
    fn: Callable[[], Any]
    weight: int = 1
    good_against: list = field(default_factory=list)  # empty = all races
    tags: list = field(default_factory=list)


BUILDS = [
    Build(name="mass_stalker", fn=mass_stalker_build, weight=1, good_against=[]),
]
