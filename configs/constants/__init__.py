import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# window name
desktop_name: str = os.getenv("DESKTOP_NAME", "")
WINDOW_NAME: str = f"{desktop_name} - Remote Desktop Connection"

# paths
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
CONFIG_DIR: Path = PROJECT_ROOT / "configs" / "bot_configs"
MACRO_CONFIG_DIR: Path = PROJECT_ROOT / "artifacts" / "macros"

MACRO_SAVE_DIR: str = str(MACRO_CONFIG_DIR)
MACRO_CONFIG_PATH: Path = MACRO_CONFIG_DIR / os.getenv("MACRO_CONFIG_FILENAME", "")
MACRO_CONFIG_PATH: str = str(MACRO_CONFIG_PATH)

TEMPLATE_DIR: Path = PROJECT_ROOT / "configs" / "detector_configs" / "templates"
RUNE_TEMPLATE_PATH: str = str(TEMPLATE_DIR / "rune.jpg")
PLAYER_TEMPLATE_PATH: str = str(TEMPLATE_DIR / "player.jpg")

# bot configs
MACRO_PLAYER_START: str = "f9"
MACRO_PLAYER_STOP: str = "f10"
MACRO_RECORD_START: str = "f7"
MACRO_RECORD_STOP: str = "f8"

BOT_SPEED: float = 13.82
BOT_OFFSET: float = 0.1