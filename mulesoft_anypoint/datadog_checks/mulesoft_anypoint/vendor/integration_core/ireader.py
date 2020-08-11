from abc import ABCMeta, abstractmethod

import six


@six.add_metaclass(ABCMeta)
class IReader:
    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    def set_add_to_queue_callback(self, add_to_queue_callback):
        pass
