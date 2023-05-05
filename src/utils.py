import requests
import time


def connection_is_active(timeout=20):
    attempts = 0
    while attempts < timeout:
        try:
            requests.head("http://www.google.com/", timeout=1)
            return True
        except requests.ConnectionError:
            time.sleep(1)

    return False
