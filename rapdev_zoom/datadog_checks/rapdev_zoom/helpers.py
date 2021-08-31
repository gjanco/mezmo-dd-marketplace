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
    if metrics["bitrate"] or metrics["avg_loss"] or metrics["jitter"] \
            or metrics["latency"] or metrics["max_loss"]:
        return True

    return False


def check_for_cpu_metrics(metrics):
    if metrics["system_max_cpu_usage"] or metrics["zoom_avg_cpu_usage"] or metrics["zoom_max_cpu_usage"] \
            or metrics["zoom_min_cpu_usage"]:
        return True

    return False


def get_country(location):
    return location.split("(")[1][:-1]


def calculate_average(value, count):
    return float(value / count)


def percentage_to_float(percentage):
    return float(percentage.split("%")[0])


def parse_milliseconds(value):
    return int(value.split(" ms")[0])


def parse_kbps(value):
    return int(value.split(" kbps")[0])
