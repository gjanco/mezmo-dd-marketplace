from datetime import datetime, timezone, timedelta
import time
import socket


def get_next_page_token(value):
    try:
        return value["pages"]["nextKey"]
    except (KeyError, IndexError, TypeError):
        return ""

def get_next_page_token_siem(value):
    try:
        return value["next_cursor"]
    except (KeyError, IndexError, TypeError):
        return ""


def get_query_time(interval):
    return (datetime.now(timezone.utc) - timedelta(seconds=interval)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]+"Z"

def get_query_time_siem(interval):
    return int(time.time()) - interval


def calculate_last_seen(last_seen):
    now = time.time()
    utc_time = datetime.strptime(last_seen, "%Y-%m-%dT%H:%M:%S.%fZ")
    return round(now - (utc_time - datetime(1970, 1, 1)).total_seconds())

def get_host_name():
    """function to get the hostname from the datadog.yaml (if present) or OS
    """

    try:
        hostname = get_config("hostname")
    except Exception:
        hostname = socket.gethostname()
        if not hostname:
            hostname = socket.getfqdn()

    return hostname
