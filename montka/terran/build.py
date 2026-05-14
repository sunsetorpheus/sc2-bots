from dataclasses import dataclass, field
from typing import Callable
from sc2.data import Race
from sharpy.plans import BuildOrder


@dataclass
class Build:
    name: str
    fn: Callable[[], BuildOrder]
    weight: int = 1
    good_against: list = field(default_factory=list)  # empty = all races
    tags: list = field(default_factory=list)           # e.g. ["aggressive", "economic"]
