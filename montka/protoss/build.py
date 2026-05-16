from dataclasses import dataclass, field
from typing import Callable, Any
from sc2.data import Race


@dataclass
class Build:
    name: str
    fn: Callable[[], Any]
    weight: int = 1
    good_against: list = field(default_factory=list)  # empty = all races
    tags: list = field(default_factory=list)
