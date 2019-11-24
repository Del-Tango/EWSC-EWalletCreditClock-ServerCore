from pack1.logger import MockLogPrinter
from pack2.system import MockSystem

class ClientTest():

    def __init__(self, **kwargs):
        mock = MockSystem()
        mock.do_shit(**kwargs)


client = ClientTest(arg1='arg1', arg2='arg2')
