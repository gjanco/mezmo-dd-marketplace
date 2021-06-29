import re
from datetime import datetime

import lxml
from bs4 import BeautifulSoup, NavigableString

SCHEDULER_PREFIX = "glide.scheduler.worker"

ANY_LETTER_NUMBER = "^[A-Za-z0-9 .]*$"  # any sequence of letters, numbers, or spaces
RFC_1123_DATE_TIME = (
    "^[A-Za-z]{3} [A-Za-z]{3} [0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2} [a-zA-Z]{3} [0-9]{4}$"
)
TRANSACTION_TIME = r"^[0-9]:[0-9]{2}:[0-9]{2}.[0-9]{3} \([0-9]* transactions, [0-9]*.[0-9]* per minute, 90% faster than [0-9]{1}:[0-9]{2}:[0-9]{2}.[0-9]{3}\)$"

TIME_STAMP = "^[0-9]{1}:[0-0]{2}:[0-9]{2}.[0-9]{3}$"

IGNORE = ["statistics_for", "at"]

METRIC_NAME_BASE = "rapdev.servicenow"
CACHE_FLUSH_METRIC_BASE = METRIC_NAME_BASE + ".cache_flushes"
ACTIVE_SESSIONS = METRIC_NAME_BASE + ".logged_in_sessions_active"
TRANSACTION_METRIC_NAME_BASE = METRIC_NAME_BASE + ".transactions"
TRANSACTION_TIME_METRIC_NAME_BASE = TRANSACTION_METRIC_NAME_BASE + ".time"
TRANSACTION_PER_MINUTE_BASE = TRANSACTION_METRIC_NAME_BASE + ".per_minute"
TRANSACTION_90P = TRANSACTION_METRIC_NAME_BASE + ".90p"

""" hard mappings """
CACHE_BUILT_KEY = "cache_built"
LOGGED_IN_SESSIONS = "logged_in_sessions"

"""
metric_name = BASE + ${key} eg: (rapdev.servicenow.) + (available_semaphores) = rapdev.servicenow.available_semaphores
"""

DATABASE_CONNECTION_POOL_DELIMITER = "status"
DATABASE_CONNECTION_HEADER = "database_connection_pool(s)"


class StatsDo:
    def __init__(self, text):
        self.soup = BeautifulSoup(text, "lxml")
        self.title = self.soup.title.string
        self.metrics = []

    def set_properties_from_soup(
        self, soup, global_tags, start_node, category_tag, sectional_tag
    ):
        database_connection_pool_count = 0
        if start_node:
            body = soup.find(start_node)
        else:
            body = soup

        for child in body.children:
            # Set Category and Sectional Tags
            try:
                previous_tag_name = child.previous.name
                if previous_tag_name == "hr":
                    category_tag = child.text.replace(" ", "_").lower().replace(":", "")
                    sectional_tag = ""  # reset section tags on new category
                    continue
                elif child.name and (
                    child.name == "strong"
                    or child.name == "b"
                    or SCHEDULER_PREFIX in child.text
                ):
                    sectional_tag = (
                        category_tag
                        + ":"
                        + child.text.replace(" ", "_").lower().replace(":", "")
                    )
                    continue
            except Exception as exception:
                print(
                    "Exception setting tags "
                    + "child "
                    + str(child)
                    + ";"
                    + repr(exception)
                )
                pass

            try:
                if not isinstance(child, NavigableString):
                    if child.name == "hr" or child.name == "br":
                        continue
                    try:
                        self.set_properties_from_soup(
                            child, global_tags, "", category_tag, sectional_tag
                        )
                        continue
                    except Exception as e:
                        print("error reading " + str(child) + "'s children\n" + repr(e))

                text = str(child)

                # if the text can't be divided into k-v pairs, not much we can do
                if text.find(":") == -1:
                    continue

                # divide text into ${KEY}:${VALUE}
                key = (
                    text[0 : text.find(":")]
                    .strip()
                    .lower()
                    .replace(" ", "_")
                    .replace("(", "")
                    .replace(")", "")
                )
                value = text[text.find(":") + 1 :].strip().lower()

                # skip ignored values
                if key in IGNORE or ".service-now.com" in key:
                    continue

                # key-values without a category or sectional tags are global tags
                if not category_tag and not sectional_tag:
                    tag = key + ":" + value
                    global_tags.append(tag)
                    continue

                # otherwise, we are dealing with a singlemetric
                tags = []
                metric_base = METRIC_NAME_BASE
                if category_tag and not sectional_tag:
                    metric_base += "." + category_tag
                if sectional_tag:
                    tags.append(sectional_tag)

                tags = global_tags + tags

                # tagging logic for database connection pools
                if category_tag == DATABASE_CONNECTION_HEADER:
                    if key == DATABASE_CONNECTION_POOL_DELIMITER:
                        database_connection_pool_count += 1
                    tags.append(
                        "database_connection_pool:"
                        + str(database_connection_pool_count)
                    )

                self.parse_line(key, value, tags, metric_base, category_tag)

            except Exception as exception:
                print(
                    "Exception parsing metric: {}; {}".format(child.encode('utf-8'), repr(exception))
                )
                pass

    def parse_line(self, key, value, tags, metric_template, category_tag):
        if key:
            metric_name = metric_template + "." + key
        else:
            metric_name = metric_template

        # Transaction Time
        if re.search(TRANSACTION_TIME, value):
            # append the time delimiter as a tag (1 day, 5min, etc)
            tags.append("time:" + key)
            tags.append("time_type:" + category_tag)
            transaction_time = value[: value.find("(")].strip()
            transaction_time_ms = self.parse_timestamp(transaction_time)

            # parse transactions per time delimiter
            self.parse_line(
                "",
                str(transaction_time_ms),
                tags,
                TRANSACTION_TIME_METRIC_NAME_BASE,
                "",
            )

            # next, look at the detailed breakdown
            transaction_time_details = (
                value[value.find("(") :].replace("(", "").replace(")", "")
            )
            transaction_time_details_split = transaction_time_details.split(",")

            num_transactions = transaction_time_details_split[0].split(" ")

            # num transactions
            self.parse_line(
                num_transactions[1], num_transactions[0], tags, METRIC_NAME_BASE, ""
            )

            transactions_per_minute = (
                transaction_time_details_split[1].strip().split(" ")[0]
            )
            # transactions per min
            self.parse_line(
                "", transactions_per_minute, tags, TRANSACTION_PER_MINUTE_BASE, ""
            )

            # 90p time
            ninetyp_time = (
                transaction_time_details_split[2].split("90% faster than")[1].strip()
            )
            ninetyp_time = self.parse_timestamp(ninetyp_time)
            self.parse_line("", str(ninetyp_time), tags, TRANSACTION_90P, "")

        # timestamp
        elif re.search(TIME_STAMP, value):
            value_time = self.parse_timestamp(value)
            self.metrics.append(
                {"name": metric_name, "value": str(value_time), "tags": tags}
            )

        # RFC 1123 time
        elif re.search(RFC_1123_DATE_TIME, value):
            now = datetime.now()
            time_zone = value.split(" ")[4]
            value_time = datetime.strptime(
                value, "%a %b %d %H:%M:%S " + time_zone + " %Y"
            )
            delta = now - value_time

            self.metrics.append(
                {"name": metric_name, "value": str(delta.total_seconds()), "tags": tags}
            )

        elif key == CACHE_BUILT_KEY:
            # cache built needs to be broken into two metrics
            cache_built_split = value.split(",")
            cache_built_time = cache_built_split[0].strip()

            # re split cache_fluches
            cache_flushes = cache_built_split[1].strip()
            # cache_flushes_key = cache_flushes.split(':')[0].strip()
            cache_flushes_value = cache_flushes.split(":")[1].strip()

            self.parse_line(key, cache_built_time, tags, METRIC_NAME_BASE, "")
            self.parse_line("", cache_flushes_value, tags, CACHE_FLUSH_METRIC_BASE, "")

        elif key == LOGGED_IN_SESSIONS:
            logged_in_sessions = value[0 : value.find("(")].strip()
            self.parse_line(key, logged_in_sessions, tags, METRIC_NAME_BASE, "")

            # active sessions
            active_sessions = value[value.find("(") + 1 : value.find("active")].strip()

            self.parse_line("", active_sessions, tags, ACTIVE_SESSIONS, "")

        # if the value is just a regular string do basic sanitation and move on
        elif re.search(ANY_LETTER_NUMBER, value):
            self.metrics.append({"name": metric_name, "value": value, "tags": tags})

        else:
            print("unable to parse " + str(key) + str(value))

    def parse_timestamp(self, transaction_time):
        transaction_time = transaction_time.split(":")
        transaction_time_ms = (
            (int(transaction_time[0]) * 3600)
            + (int(transaction_time[1]) * 60)
            + float(transaction_time[2])
        ) * 1000
        return transaction_time_ms
