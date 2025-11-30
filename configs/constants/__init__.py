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

BOT_CONFIG_PATH: Path = CONFIG_DIR / "bot_config.yaml"
PATTERN_CONFIG_PATH: Path = CONFIG_DIR / "pattern_config.yaml"
BOT_CONFIG_PATH = str(BOT_CONFIG_PATH)
PATTERN_CONFIG_PATH = str(PATTERN_CONFIG_PATH)

# bot configs
BOT_SPEED: float = 13.82
BOT_OFFSET: float = 0.1