from dataclasses import dataclass
from typing import Dict, List, Literal, Optional

@dataclass
class Point:
    name: str
    x: int
    y: int

@dataclass
class SummonPoint:
    name: str      # e.g. "summon1"
    point: str     # e.g. "summon1_point"


@dataclass
class HuntingStep:
    from_: str              
    to: str                 
    jumps: int              
    attack: str             
    type: str = "sweep"     
    style: Literal["hold", "press"] = "hold"  

@dataclass
class PatternConfig:
    map_name: str
    points: Dict[str, Point]
    summons: List[SummonPoint]
    hunting_loop: List[HuntingStep]