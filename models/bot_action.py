from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class ActionConfig:
    name: str
    key: Optional[str]
    cooldown: Optional[int]


@dataclass
class BotConfig:
    movement: Dict[str, ActionConfig]
    attacks: Dict[str, ActionConfig]
    buffs: Dict[str, ActionConfig]
    specials: Dict[str, ActionConfig]

    def get(self, category: str, action: str) -> ActionConfig:
        group = getattr(self, category, {})
        if action not in group:
            raise KeyError(f"Action '{action}' not found in category '{category}'")
        return group[action]

    def get_key(self, category: str, action: str) -> Optional[str]:
        return self.get(category, action).key
