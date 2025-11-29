import time
from typing import Any
import sys

from configs import constants
from exception import CustomException
from logger import logging

class RunTasks():
    def __init__(self):
        try:
            self.window_name: str = constants.WINDOW_NAME

        except Exception as e:
            raise CustomException(e, sys) from e

    def run_vision(self):
        try:
            logging.info("vision thread running...")
            print(f"{self.window_name}")
            # TODO
        except Exception as e:
            raise CustomException(e, sys) from e

    def run_bot(self):
        print("bot logic running...")
        # TODO

    def run_ai(self):
        print("ai logic running...")
        # TODO

    def start_program(self):
        self.run_vision()

if __name__ == "__main__":
    try:
        print("quit - press 'q'")
        time.sleep(2)

        entry_point = RunTasks()
        entry_point.start_program()

    except Exception as e:
        raise CustomException(e, sys) from e