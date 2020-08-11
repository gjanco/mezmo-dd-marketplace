from abc import ABCMeta, abstractmethod

import six


@six.add_metaclass(ABCMeta)
class ILogger:
    @abstractmethod
    def debug(self, message):
        pass

    @abstractmethod
    def info(self, message):
        pass

    @abstractmethod
    def warning(self, message):
        pass

    @abstractmethod
    def error(self, message):
        pass
