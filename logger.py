from datetime import datetime
import os

LOG_PATH = "data/logs/system.log"

def log(message: str):
    os.makedirs("data/logs", exist_ok=True)

    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} - {message}\n")
