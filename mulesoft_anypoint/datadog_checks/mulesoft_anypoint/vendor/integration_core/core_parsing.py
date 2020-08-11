import re
from abc import ABCMeta, abstractmethod

import six

RE_CURLY_BRACES_KEYS = "{[^}]*?}"
RE_NUMBER = "[0-9.]+"
RE_NOT_NUMBER = "[^0-9.]+"
RE_DATE = (
    "\\d{4}-[01]\\d-[0-3]\\dT[0-2]\\d:[0-5]\\d:[0-5]\\d\\.\\d+([+-][0-2]\\d:[0-5]\\d|Z)"
)


@six.add_metaclass(ABCMeta)
class IParser:
    @abstractmethod
    def get_list(self, expr, data):
        raise NotImplementedError

    @abstractmethod
    def get_set(self, expr, data):
        raise NotImplementedError

    @abstractmethod
    def get_one(self, expr, data):
        raise NotImplementedError


# pylint: disable=W0223
@six.add_metaclass(ABCMeta)
class BaseParser(IParser):
    def get_set(self, expr, data):
        parsed_list = self.get_list(expr, data)
        try:
            return list(dict.fromkeys(parsed_list))
        except TypeError:
            return parsed_list


class RegexParser(BaseParser):
    def get_list(self, expr, data):
        return re.findall(expr, data)

    def get_one(self, expr, data):
        match = re.search(expr, data)
        if match:
            return match.group(0)
        return None
