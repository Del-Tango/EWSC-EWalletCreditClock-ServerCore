import datetime


class MockLogPrinter():

    def log(self, *args):
        for item in args:
            print('{} Log Message - {}'.format(datetime.datetime.now(), item))
        return True
