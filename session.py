"""Represent a user session
"""

class Session(object):

    def __init__(self):
        self.current_code = None

    def updateAlgoCode(self, code):
        self.current_code = code
        return self

    def runBacktest(self):
        return self

class BacktestMachine(object):

    _producer_types = {
        'GENERATOR_MODE' : GeneratorProducer,
        'ZIPLINE_MODE' : ZiplineProducer
    }

    def __init__(self, code, mode='GENERATOR_MODE'):
        self._producer = BacktestMachine._producer_types[mode](code)
        self._consumer = WebsocketServerConsumer()

    def getEndpoint(self):
        return self._consumer.getClientEndpoint()

    def start(self):
        self._producer.start()
        self._consumer.start()

    def stop(self):
        self._producer.stop()
        self._consumer.stop()
        self._producer.join()
        self._consumer.join()

def f(algoCode, mode):

    def noop(*args, **kwargs):
        pass

    if mode == 'GENERATOR_MODE':
        code = compile(algoCode, '<string>', 'exec')
        namespace = {}
        exec(code, namespace)
        _gen = namespace.get('fun', noop)

        producer = GeneratorProducer()
        
        gthread = GeneratorThread(_gen)
        uri = gthread.get_wsuri()
        return uri
    elif mode == 'ZIPLINE_MODE':
        pass
