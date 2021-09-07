from datetime import datetime


def get_days_since_date(timestamp):
    last_seen_date = timestamp.split("T")[0]

    date_format = "%Y-%m-%d"

    last_seen_datetime = datetime.strptime(last_seen_date, date_format)
    current_datetime = datetime.today()

    delta = current_datetime - last_seen_datetime

    return delta.days

