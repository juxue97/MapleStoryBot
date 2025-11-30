import sys
import time
from threading import Thread, Lock
from typing import Callable, Dict

from exception import CustomException
from logger import logging

from models.bot_action import BotConfig, ActionConfig
from models.points import HuntingStep, PatternConfig, Point

from utils import random_num
from utils.bot import BotUtils
from utils.bot.background_input import BackgroundInput
from utils.bot.movement_controller import MovementController
from utils.enum import BotState

class AutoBot:
    buffer_time: float = 0.1
    initializing_time: float = 2.5

    def __init__(
        self,
        window_name: str,
        bot_config_path: str,
        pattern_config_path: str,
        get_position: Callable[[], tuple[int, int]],
    ):
        try:
            self.lock = Lock()

            # keys / actions
            self.utils: BotUtils = BotUtils()
            self.config: BotConfig = self.utils.load_bot_config(path=bot_config_path)

            # input
            self.input: BackgroundInput = BackgroundInput(window_name=window_name)
            self.utils.input = self.input

            # pattern (points + hunting loop + summons bindings)
            self.pattern: PatternConfig = self.utils.load_pattern_config(path=pattern_config_path)

            # movement controller
            self.mover: MovementController = MovementController(utils=self.utils, get_position=get_position)

            # build Point objects from pattern.points
            self.points: dict[str, Point] = dict(self.pattern.points)

            # cooldown tracking: summon name -> next ready time
            self.summon_next_ready: Dict[str, float] = {}
            self._init_summon_cooldowns()

            # rune flag (set by other part of system)
            self.rune_flag: bool = False

            # state machine
            self.state: int = BotState.INITIALIZING

            # run control
            self.stopped: bool = True

            logging.info("AutoBot initialized successfully.")
        except Exception as e:
            logging.error(f"Error initializing AutoBot: {e}")
            raise CustomException(e, sys) from e

    # -------------------------------------------------
    #  PUBLIC API: start/stop + external rune flag
    # -------------------------------------------------
    def start(self) -> None:
        try:
            if not self.stopped:
                logging.warning("AutoBot.start() called but bot is already running.")
                return

            self.stopped = False
            t = Thread(target=self.run, daemon=True)
            t.start()
            logging.info("AutoBot thread started.")
            time.sleep(self.buffer_time)
        except Exception as e:
            logging.error(f"Error starting AutoBot: {e}")
            raise CustomException(e, sys) from e

    def stop(self) -> None:
        try:
            self.stopped = True
            logging.info("AutoBot thread stop requested.")
        except Exception as e:
            logging.error(f"Error stopping AutoBot: {e}")
            raise CustomException(e, sys) from e

    def set_rune_flag(self, value: bool) -> None:
        """Called externally when vision detects rune (or clears it)."""
        try:
            with self.lock:
                self.rune_flag = value
            logging.info(f"Rune flag set to {value}.")
        except Exception as e:
            logging.error(f"Error setting rune flag: {e}")
            raise CustomException(e, sys) from e

    # -------------------------------------------------
    #  MAIN LOOP WITH STATE MACHINE
    # -------------------------------------------------
    def run(self) -> None:
        try:
            logging.info("AutoBot main loop started.")

            while not self.stopped:
                with self.lock:
                    current_state = self.state
                    rune = self.rune_flag

                if current_state == BotState.INITIALIZING:
                    logging.info("State: INITIALIZING")
                    time.sleep(self.initializing_time)
                    # Any initial reset / timing can go here
                    # For now we immediately go to placement
                    self._transition_to(BotState.PLACEMENT)

                elif current_state == BotState.PLACEMENT:
                    logging.info("State: PLACEMENT (summon placement)")
                    self.run_summon_cycle()
                    self._transition_to(BotState.HUNTING)

                elif current_state == BotState.HUNTING:
                    logging.info("State: HUNTING")
                    self.run_hunting_loop_once()

                    # after each full hunting loop:
                    with self.lock:
                        rune = self.rune_flag

                    if rune:
                        logging.info("Rune detected - switching to RUNE state.")
                        self._transition_to(BotState.RUNE)
                    elif self._is_any_summon_ready():
                        logging.info("Summon cooldown ready - switching to PLACEMENT state.")
                        self._transition_to(BotState.PLACEMENT)
                    else:
                        # stay in hunting
                        pass

                elif current_state == BotState.RUNE:
                    logging.info("State: RUNE (rune-clearing mode)")
                    self._clear_rune()
                    # After finishing rune: re-initialize cycle
                    self._transition_to(BotState.INITIALIZING)

                else:
                    logging.warning(f"Unknown bot state '{current_state}', resetting to INITIALIZING.")
                    self._transition_to(BotState.INITIALIZING)

                time.sleep(0.01)

            logging.info("AutoBot main loop exited.")
        except Exception as e:
            logging.error(f"AutoBot runtime error: {e}")
            raise CustomException(e, sys) from e

    def _transition_to(self, new_state: int) -> None:
        with self.lock:
            logging.info(f"Bot state transition: {self.state} -> {new_state}")
            self.state = new_state

    # -------------------------------------------------
    #  COOLDOWNS (with lock)
    # -------------------------------------------------
    def _init_summon_cooldowns(self) -> None:
        try:
            now = time.time()
            with self.lock:
                for s in self.pattern.summons:
                    try:
                        cfg: ActionConfig = self.config.get("specials", s.name)
                    except KeyError:
                        logging.warning(f"Summon '{s.name}' not found in specials config; skipping cooldown init.")
                        continue
                    self.summon_next_ready[s.name] = now
            logging.info(f"Summon cooldowns initialized: {list(self.summon_next_ready.keys())}")
        except Exception as e:
            logging.error(f"Error initializing summon cooldowns: {e}")
            raise CustomException(e, sys) from e

    def _mark_summon_used(self, summon_name: str) -> None:
        try:
            cfg: ActionConfig = self.config.get("specials", summon_name)
            cooldown = cfg.cooldown
            with self.lock:
                if cooldown is None:
                    self.summon_next_ready[summon_name] = time.time()
                else:
                    self.summon_next_ready[summon_name] = time.time() + cooldown
            logging.debug(f"Summon '{summon_name}' used; cooldown={cooldown}.")
        except KeyError:
            logging.warning(f"_mark_summon_used called for unknown summon '{summon_name}'.")
        except Exception as e:
            logging.error(f"Error marking summon '{summon_name}' as used: {e}")
            raise CustomException(e, sys) from e

    def _is_any_summon_ready(self) -> bool:
        try:
            now = time.time()
            with self.lock:
                for s in self.pattern.summons:
                    ready_at = self.summon_next_ready.get(s.name, 0)
                    if now >= ready_at:
                        return True
            return False
        except Exception as e:
            logging.error(f"Error checking summon readiness: {e}")
            raise CustomException(e, sys) from e

    # -------------------------------------------------
    #  MOVEMENT + BASIC OPS
    # -------------------------------------------------
    def go_to(self, point_name: str) -> None:
        try:
            point = self.points[point_name]
            logging.info(f"Moving to point '{point_name}' at ({point.x}, {point.y}).")
            self.mover.move_to_point(point)
        except KeyError:
            logging.error(f"Point '{point_name}' not defined.")
            raise
        except Exception as e:
            logging.error(f"Error moving to point '{point_name}': {e}")
            raise CustomException(e, sys) from e

    # -------------------------------------------------
    #  SUMMON CYCLE (PLACEMENT STATE)
    # -------------------------------------------------
    def run_summon_cycle(self) -> None:
        try:
            logging.info("Starting summon placement cycle.")

            # always back to very first initial point
            self.go_to("start_left")

            for s in self.pattern.summons:
                try:
                    special_cfg: ActionConfig = self.config.get("specials", s.name)
                except KeyError:
                    logging.warning(f"Summon '{s.name}' not found in config.specials; skipping.")
                    continue

                if not special_cfg.key:
                    logging.debug(f"Summon '{s.name}' has no key bound; skipping.")
                    continue

                logging.info(f"Placing summon '{s.name}' at point '{s.point}'.")
                self.go_to(s.point)
                time.sleep(0.2)

                self.utils.press_action("specials", s.name)
                self._mark_summon_used(s.name)

                time.sleep(0.1)

            # after all summons, move to starting right to begin hunting
            self.go_to("start_right")
            logging.info("Summon placement cycle completed.")
        except Exception as e:
            logging.error(f"Error during summon cycle: {e}")
            raise CustomException(e, sys) from e

    # -------------------------------------------------
    #  HUNTING LOOP (HUNTING STATE)
    # -------------------------------------------------
    def run_hunting_loop_once(self) -> None:
        try:
            for step in self.pattern.hunting_loop:
                if step.type == "sweep":
                    logging.info(
                        f"Running sweep from '{step.from_}' to '{step.to}' "
                        f"jumps={step.jumps}, attack={step.attack}, style={getattr(step, 'style', 'hold')}"
                    )
                    self._run_sweep(step)
                else:
                    logging.warning(f"Unknown hunting step type '{step.type}'; skipping.")
        except Exception as e:
            logging.error(f"Error in hunting loop: {e}")
            raise CustomException(e, sys) from e

    def _run_sweep(self, step: HuntingStep) -> None:
        try:
            start_point = self.points[step.from_]
            end_point = self.points[step.to]

            self.mover.move_to_point(start_point)

            move_action = "move_left" if end_point.x < start_point.x else "move_right"
            jumps = step.jumps
            attack_action = step.attack
            style = getattr(step, "style", "hold")

            if style == "hold":
                with self.utils.hold_action("attacks", attack_action):
                    for _ in range(jumps):
                        with self.utils.hold_action("movement", move_action):
                            self.utils.press_action("movement", "jump", 2, random_num(0.07,0.12))
                            time.sleep(0.10)
            elif style == "press":
                for _ in range(jumps):
                    with self.utils.hold_action("movement", move_action):
                        self.utils.press_action("movement", "jump", 2, random_num(0.07, 0.12))
                        self.utils.press_action("attacks", attack_action)
                        time.sleep(0.10)
            else:
                logging.warning(f"Unknown sweep style '{style}', defaulting to 'hold'.")
                with self.utils.hold_action("attacks", attack_action):
                    for _ in range(jumps):
                        with self.utils.hold_action("movement", move_action):
                            self.utils.press_action("movement", "jump", 2, random_num(0.07, 0.12))
                            time.sleep(0.10)
        except Exception as e:
            logging.error(f"Error running sweep step: {e}")
            raise CustomException(e, sys) from e

    # -------------------------------------------------
    #  RUNE STATE (TODO)
    # -------------------------------------------------
    def _clear_rune(self) -> None:
        """
        TODO: Implement rune-clearing logic.
        For now, just simulate some wait and clear the rune_flag.
        """
        try:
            logging.info("Entering rune clear routine (TODO implementation).")
            # TODO: add actual movement + arrow input etc.

            time.sleep(2.0)  # simulate work

            with self.lock:
                self.rune_flag = False

            logging.info("Rune clear routine finished; rune_flag reset to False.")
        except Exception as e:
            logging.error(f"Error in rune clear routine: {e}")
            raise CustomException(e, sys) from e
