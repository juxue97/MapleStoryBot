import random
import win32gui  # type: ignore
import sys
import yaml
import os

from exception import CustomException

def random_num(lb, ub) -> float:
    return float(f"{random.uniform(lb, ub):.3f}")

def find_window_by_title(keyword: str):
    result = []

    def enum_handler(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return
        title = win32gui.GetWindowText(hwnd)
        if keyword.lower() in title.lower():
            result.append(hwnd)

    win32gui.EnumWindows(enum_handler, None)
    return result[0] if result else None

def read_yaml_file(file_path: str) -> dict:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    except Exception as e:
        raise CustomException(e, sys) from e


def write_yaml_file(file_path: str, content: object, replace: bool = False) -> None:
    """
    Safely write YAML content to file.

    Args:
        file_path: Full path including filename.yml
        content: Python object to write
        replace: If True, remove the file if it exists before writing
    """
    try:
        dir_name = os.path.dirname(file_path)
        os.makedirs(dir_name, exist_ok=True)

        if replace and os.path.exists(file_path):
            os.remove(file_path)

        with open(file_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(content, f, sort_keys=False)

    except Exception as e:
        raise CustomException(e, sys) from e