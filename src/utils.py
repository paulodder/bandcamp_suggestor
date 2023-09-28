import requests
import time
import re
import json
import uuid
from datetime import datetime
from pathlib import Path


def remove_links(input_string):
    # This regular expression pattern matches most URLs
    pattern = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
    # Using re.sub() to replace URLs with an empty string
    return re.sub(pattern, "", input_string)


def connection_is_active(timeout=10):
    attempts = 0
    while attempts < timeout:
        try:
            requests.head("http://www.google.com/", timeout=2)
            return True
        except (requests.ConnectionError, requests.exceptions.ReadTimeout):
            time.sleep(1)

    return False


def get_date_str(file_format=False):
    # Get today's date
    now = datetime.now()

    # If file_format is True, return the date in 'dd_mm_yyyy' format
    if file_format:
        return now.strftime("%d_%m_%Y")

    # Define suffixes
    suffixes = {1: "st", 2: "nd", 3: "rd"}

    # I'm checking for 10-20 because those are the digits that
    # don't follow the normal counting scheme. Note, it's
    # elif, so it only checks for 4-20 if it's not 10-20
    if 10 <= now.day <= 20:
        suffix = "th"
    else:
        # the last digit is all we care about
        suffix = suffixes.get(now.day % 10, "th")

    # Now format the date to the format '3rd of July'
    return now.strftime(f"%-d{suffix} of %B")


def clear_directory_recursive(directory_path, include_topdir=True):
    try:
        path = Path(directory_path)
        for item in path.rglob("*"):
            if item.is_file():
                item.unlink()  # Remove file
            elif item.is_dir():
                item.rmdir()  # Remove directory
        if include_topdir:
            path.rmdir()  # Remove the top-level directory itself
    except FileNotFoundError:
        print(f"Directory {directory_path} does not exist.")
    except OSError as e:
        print(f"An error occurred while removing the directory: {e}")


def generate_paths(dir_path, names):
    paths = {}
    timestamp = str(int(time.time()))
    rand_str = str(uuid.uuid4())
    for name in names:
        paths[name] = Path(dir_path) / f"{timestamp}_{name}_{rand_str}.mp3"
    return paths


def load_json(fpath):
    try:
        with open(fpath, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(fpath, "does not exist")
        return {}


def save_json(fpath, obj):
    with open(fpath, "w") as f:
        json.dump(obj, f, indent=2)


def change_suffix(fpath, new_suffix):
    fpath = Path(fpath)
    return fpath.parent / (fpath.stem + new_suffix)
