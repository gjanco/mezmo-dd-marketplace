# Copyright (C) 2023 Crest Data Systems.
# All rights reserved

from datetime import datetime
from typing import Any, Dict, List, Union

from dateutil.parser import parse as dateutil_parse


def field_parser(event: Dict, fields: List) -> Dict:
    """Parses multi-level dict structure's fields to single level dictionary

    :param event: event data dictionary
    :type event: dict
    :param fields: fields to be extracted from event data
    :type fields: list

    :return: resulted parsed event data
    :rtype: dict
    """
    result = {}
    for field in fields:
        data = None
        field_keys = field.split(".")
        for index, key in enumerate(field_keys):
            index += 1
            data = data.get(key) if data else event.get(key)
            if isinstance(data, list) and index < len(field_keys):
                _data = []
                child_field = ".".join(field_keys[index:])
                for _event in data:
                    _result = field_parser(_event, [child_field])
                    if not (is_empty(_result.get(child_field)) or _result.get(child_field) == "-"):
                        _data.append(_result.get(child_field))
                data = _data
                break
            elif not data:
                break

        result[field] = "-" if is_empty(data) else data

    return result


def field_alias_generator(event, alias):
    """Generates alias fields from event data.

    :param event: event data
    :type event: dict
    :param alias: alias fields
    :type alias: dict
    """
    result = {}
    for new_field in alias:
        if not is_empty(event.get(new_field)):
            result[new_field] = event[new_field]
            continue
        for old_field in alias[new_field]:
            if not is_empty(event.get(old_field)):
                result[new_field] = event[old_field]
                break

        if is_empty(result.get(new_field)):
            result[new_field] = "-"

    return result


def tag_generator(event, fields):
    """Generates tag list from event with provided field name list"""
    tags = []
    for field in fields:
        tags.append(f"{field}:{event.get(field)}")
    return tags


def is_true(val: Union[str, int]) -> bool:
    """Checks if value is true."""
    value = str(val).strip().upper()
    if value in ("1", "TRUE", "T", "Y", "YES"):
        return True
    return False


def is_float(val: Any) -> bool:
    """Checks if value is a float value."""
    try:
        float(val)
        return True
    except (ValueError, TypeError):
        return False


def is_bool(val: Any) -> bool:
    """Checks if value is of boolean type or not."""
    return isinstance(val, bool)


def is_empty(val: Any) -> bool:
    """Checks whether value is empty string, None value or empty object."""
    return not (val or is_float(val) or is_bool(val))


def generate_metrics(
    response,
    panel_name,
    event_fields,
    alias_fields,
    tag_fields,
    metric_fields,
    is_count=False,
    timestamp_field=None,
):
    """Generate and returns metrics list with tags."""
    metric_list = []
    for record in response:
        raw_event = field_parser(record, event_fields)
        event = field_alias_generator(raw_event, alias_fields)
        tags = tag_generator(event, tag_fields)
        for metric_field in metric_fields:
            metric_prefix = ".".join([panel_name, metric_field])
            if is_count:
                metric_prefix += ".count"
            metric_list.append(
                [
                    metric_prefix,
                    1 if is_count else event.get(metric_field, 0),
                    tags,
                    event.get(timestamp_field) if timestamp_field else None,
                ]
            )

    return metric_list


def generate_logs(response, event_fields, alias_fields, conditions=None):
    """Generates and returns logs list with tags."""
    logs_list = []
    for record in response:
        raw_event = field_parser(record, event_fields)
        event = field_alias_generator(raw_event, alias_fields)
        if not conditions or condition_check(event, conditions):
            logs_list.append(event)
    return logs_list


def condition_check(event, conditions):
    """Checks whether given event passes the conditions."""
    for field in conditions:
        for condition in conditions[field]:
            value = event.get(field)
            if (condition == "not_empty" and is_empty(value)) or (
                condition == "not_zero" and is_float(value) and float(value) == 0
            ):
                return False

    return True


def get_epoch_timestamp(value):
    """Converts the provided datetime value to the datetime.datetime object."""
    if isinstance(value, datetime):
        return value.timestamp()
    try:
        return dateutil_parse(value).timestamp()
    except Exception:
        return None
