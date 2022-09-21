import jwt
import time


def generate_token(api_key, api_secret):
    token = jwt.encode(
        {"iss": api_key, "exp": time.time() + 60},
        api_secret,
        algorithm='HS256'
    )
    
    if float(jwt.__version__.split('.')[0]) < 2:
        token = token.decode('utf-8')

    return token


VALID_METRICS = [
    "bitrate",
    "avg_loss",
    "jitter",
    "latency",
    "max_loss"
]
def check_for_metrics(metrics):
    for VALID_METRIC in VALID_METRICS:
        if metrics.get(VALID_METRIC):
            return True

    return False


VALID_CPU_METRICS = [
    "system_max_cpu_usage",
    "zoom_avg_cpu_usage",
    "zoom_max_cpu_usage",
    "zoom_min_cpu_usage"
]
def check_for_cpu_metrics(metrics):
    for VALID_CPU_METRIC in VALID_CPU_METRICS:
        if metrics.get(VALID_CPU_METRIC):
            return True

    return False


def get_country(location):
    if location:
        return location.split("(")[1][:-1]
    else:
        return "not_available"


def calculate_average(value, count):
    if value and count:
        return float(value / count)
    else:
        return float()


def percentage_to_float(percentage):
    if percentage:
        return float(percentage.split("%")[0])
    else:
        return float()


def parse_milliseconds(value):
    if value:
        return int(value.split(" ms")[0])
    else:
        return int()


def parse_kbps(value):
    if value:
        return int(value.split(" kbps")[0])
    else:
        return int()


def get_room_location_tags(location_id, locations_dict):
    """"""
    tags = []

    # This is a reverse ordered list (room --> parent --> parent 2 --> final parent)
    location_structure = locations_dict.get("structures")

    for structure in location_structure:
        # Get the current location's name
        location_name = locations_dict.get(structure, {}).get(location_id, {}).get("name")
        
        # Update the location id to the parent's location id
        location_id = locations_dict.get(structure, {}).get(location_id, {}).get("parent_id")

        tags.append("zoom_room_{}:{}".format(structure, location_name))

    return tags
