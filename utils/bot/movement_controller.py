import time
from typing import Callable

from configs.constants import BOT_OFFSET, BOT_SPEED
from models.points import Point
from utils.bot import BotUtils


class MovementController:
    """
    Generic navigator that moves your character from current (x,y)
    to a target (x,y) using:
      - horizontal left/right holds (based on movement speed)
      - vertical up/down patterns (down+jump, up_rope)
    """
    def __init__(
        self,
        utils: BotUtils,
        get_position: tuple[int, int],
        x_tolerance: int = 5,
        y_tolerance: int = 5,
        speed: float = BOT_SPEED,
        offset: float = BOT_OFFSET,
    ):
        self.utils = utils
        self.get_position = get_position
        self.x_tol = x_tolerance
        self.y_tol = y_tolerance
        self.speed = speed
        self.offset = offset

    # --------- PUBLIC API ---------
    def move_to_point(self, point: Point):
        """
        Move to a target coordinate:
        - horizontally adjust
        - vertically adjust using patterns
        """
        self._move_horizontally_to(point.x)
        self._move_vertically_to(point.y)

    # --------- INTERNAL HELPERS ---------
    def _move_horizontally_to(self, target_x: int):
        """
        Move horizontally by *holding* left/right based on BOT_SPEED.
        We:
          - compute distance in x
          - compute how long to hold the key: time = dist / speed - offset
          - loop until within tolerance or max_steps reached
        """
        max_steps = 20  # safety; each step can be a long-ish hold

        for _ in range(max_steps):
            cur_x, _ = self.get_position
            diff = target_x - cur_x

            # close enough
            if abs(diff) <= self.x_tol:
                break

            # direction & remaining distance (minus tolerance so we don't overshoot too much)
            direction_action = "move_right" if diff > 0 else "move_left"
            remaining = max(0.0, abs(diff) - self.x_tol)

            # seconds = distance / speed
            hold_time = (remaining / self.speed) - self.offset
            # clamp
            hold_time = max(0.02, min(hold_time, 1.0))  # don't go too tiny or too huge in one go

            # Hold the direction key for computed time
            with self.utils.hold_action("movement", direction_action):
                time.sleep(hold_time)

            # small delay to let vision update
            time.sleep(0.03)

    def _move_vertically_to(self, target_y: int):
        """
        Assuming image coords: y increases DOWNwards.

        - If current_y < target_y -> player is ABOVE -> need to go DOWN.
        - If current_y > target_y -> player is BELOW -> need to go UP.
        """
        max_steps = 100
        for _ in range(max_steps):
            _, cur_y = self.get_position
            diff = target_y - cur_y

            if abs(diff) <= self.y_tol:
                break

            if diff > 0:
                # target lower -> go down
                self._vertical_down_step()
            else:
                # target higher -> go up
                self._vertical_up_step()

            time.sleep(0.05)

    # --------- VERTICAL PATTERNS ---------
    def _vertical_down_step(self):
        """
        Downward pattern:
        - hold down
        - press jump
        """
        with self.utils.hold_action("movement", "move_down"):
            self.utils.press_action("movement", "jump")
            time.sleep(0.15)  # tweak

    def _vertical_up_step(self):
        """
        Upward pattern:
        - press up_rope
        - wait a bit for rope climb
        """
        self.utils.press_action("movement", "up_rope")
        time.sleep(0.30)  # tweak so one rope cast climbs ~1 platform
