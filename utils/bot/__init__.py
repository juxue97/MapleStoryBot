from typing import Optional

from models.bot_action import ActionConfig, BotConfig
from models.points import HuntingStep, PatternConfig, Point, SummonPoint
from utils.bot.background_input import BackgroundInput
from utils.reader import read_yaml_file

class BotUtils:
    def __init__(self):
        self.config: BotConfig = None
        self.input: Optional[BackgroundInput] = None

    def _load_group(self, raw_list):
        result = {}
        for item in raw_list or []:
            name = item.get("name")
            if not name:
                continue
            result[name] = ActionConfig(
                name=name,
                key=item.get("key"),
                cooldown=item.get("cooldown"),
            )
        return result

    def load_bot_config(self, path: str) -> BotConfig:
        data = read_yaml_file(path)

        movement = self._load_group(data.get("movement"))
        attacks = self._load_group(data.get("attacks"))
        buffs = self._load_group(data.get("buffs"))
        specials = self._load_group(data.get("specials"))

        self.config = BotConfig(
            movement=movement,
            attacks=attacks,
            buffs=buffs,
            specials=specials,
        )

        return self.config

    @staticmethod
    def load_pattern_config(path: str) -> PatternConfig:
        """Load the map/pattern YAML file."""
        data = read_yaml_file(path)

        # Load points (coordinates)
        raw_points = data.get("points", {})
        points = {
            name: Point(name=name, x=info["x"], y=info["y"])
            for name, info in raw_points.items()
        }

        # Load summons (name -> point)
        summons = [
            SummonPoint(name=item["name"], point=item["point"])
            for item in data.get("summons", []) or []
        ]

        # Load hunting loop steps
        hunting_loop = []
        for step in data.get("hunting_loop", []) or []:
            hunting_loop.append(
                HuntingStep(
                    type=step["type"],
                    from_=step["from"],
                    to=step["to"],
                    jumps=step.get("jumps", 0),
                    attack=step["attack"],
                    style=step.get("style", "hold"),
                )
            )

        return PatternConfig(
            map_name=data["map_name"],
            points=points,
            summons=summons,
            hunting_loop=hunting_loop
        )

    def key_for(self, category: str, action: str) -> Optional[str]:
        return self.config.get_key(category, action)

    def press_action(self, category: str, action: str, presses: int = 1, interval: float = 0.0):
        key = self.key_for(category, action)
        if key:
            self.input.press(key, presses=presses, interval=interval)

    def hold_action(self, category: str, action: str):
        key = self.key_for(category, action)
        if key:
            return self.input.hold(key)
        raise ValueError(f"Holding action '{action}' (category '{category}') has no key")

    def key_down_action(self, category: str, action: str):
        key = self.key_for(category, action)
        if key:
            self.input.key_down(key)

    def key_up_action(self, category: str, action: str):
        key = self.key_for(category, action)
        if key:
            self.input.key_up(key)