import time
import json
from decouple import config
from pathlib import Path


class TimeManager:
    def __init__(self):
        self.file_path = Path(config("PROJECT_DIR")) / "timestamp.json"

        # Try to read the last used time from the JSON file.
        try:
            with open(self.file_path, "r") as f:
                time_json = json.load(f)
                self.last_used = time_json.get("last_used", 0)
        except FileNotFoundError:
            self.last_used = 0

    def update_time(self):
        """Updates the 'last_used' time and saves it to a JSON file."""
        current_time = int(time.time())
        self.last_used = current_time

        # Save to JSON file
        with open(self.file_path, "w") as f:
            json.dump({"last_used": self.last_used}, f)

        return self.last_used

    def get_last_used_time(self):
        """Retrieves the last used time without updating it."""
        return self.last_used

    def time_difference_in_minutes(self):
        """Calculates the time difference between now and the last used time, in minutes."""
        current_time = int(time.time())
        time_difference = current_time - self.last_used
        return time_difference // 60
