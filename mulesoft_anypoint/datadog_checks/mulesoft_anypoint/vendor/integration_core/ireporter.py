from abc import ABCMeta, abstractmethod
from enum import Enum

import six


class ReportItemType(Enum):
    COUNT = 1
    GAUGE = 2
    SERVICE_CHECK = 3


class CheckStatus(Enum):
    OK = 0
    WARNING = 1
    CRITICAL = 2


class ReportItem:
    def __init__(
        self,
        name=None,
        report_type=None,
        value=None,
        tags=None,
        message=None,
        extras=None,
        json_data=None,
    ):
        if json_data:
            self.name = json_data["name"]
            self.report_type = ReportItemType(json_data["report_type"])
            self.value = json_data["value"]
            self.tags = json_data.get("tags") or None
            self.message = json_data.get("message") or None
            self.extras = json_data.get("extras") or None

        else:
            self.name = name
            self.report_type = report_type
            self.value = value
            self.tags = tags
            self.message = message
            self.extras = extras

    def set_by_index(self, value, index):
        if index == 0:
            self.name = value
        if index == 1:
            self.report_type = value
        if index == 2:
            self.value = value
        if index == 3:
            self.tags = value
        if index == 4:
            self.message = value
        if index == 5:
            self.extras = value

    def copy(self):
        return ReportItem(
            name=self.name,
            report_type=self.report_type,
            value=self.value,
            tags=self.tags,
            message=self.message,
            extras=self.extras,
        )

    def update(self, source):
        self.name = source.name
        self.report_type = source.report_type
        self.value = source.value
        self.tags = source.tags
        self.message = source.message
        self.extras = source.extras


@six.add_metaclass(ABCMeta)
class IReporter:
    @abstractmethod
    def report_metric(self, report_item):
        pass
