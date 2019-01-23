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
