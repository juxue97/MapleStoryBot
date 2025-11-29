import os
from dotenv import load_dotenv

load_dotenv()

desktop_name: str = os.getenv("DESKTOP_NAME", "")
WINDOW_NAME: str = f"{desktop_name} - Remote Desktop Connection"
