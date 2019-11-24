from ..pack1.logger import MockLogPrinter as log


class MockSystem():

    def do_shit(self, **kwargs):
        for item in kwargs:
            log.log(item)
