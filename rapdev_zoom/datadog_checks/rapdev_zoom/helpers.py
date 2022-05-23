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


def check_for_metrics(metrics):
    if any(
        metrics.get("bitrate"), metrics.get("avg_loss"), metrics.get("jitter"), metrics("latency"), metrics("max_loss")
    ):
        return True

    return False


def check_for_cpu_metrics(metrics):
    if any(
        metrics.get("system_max_cpu_usage"),
        metrics.get("zoom_avg_cpu_usage"),
        metrics.get("zoom_max_cpu_usage"),
        metrics.get("zoom_min_cpu_usage"),
    ):
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

def get_room_location_tags(location_id, locations):
    tags = []
    locationtype = ""
    while locationtype != "country":
        for i in locations:
            if location_id == i.get("id"):
                tags.append("zoom_room_{}:{}".format(i.get("type", ""), i.get("name", "")))

                if i.get("type") != "country":
                    location_id = i.get("parent_location_id", "")
                else:
                    locationtype = "country"
                    break
    return tags