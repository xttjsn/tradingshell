"""High level abstraction of the logic of running a backtest - BacktestMachine
"""
from threading import Lock, Condition, Thread
import asyncio
import websockets
from abc import ABCMeta, abstractmethod

class Endpoint(object):
    def __init__(self):
        self._queue = []
        self._lock = Lock()
        self._cond = Condition(self._lock)
        self._ended = False

    def give(self, data):
        self._cond.acquire()
        self._queue.append(data)
        self._cond.notify_all()
        self._cond.release()

    def end(self):
        self._cond.acquire()
        self._ended = True
        self._cond.notify_all()
        self._cond.release()
    
    def take(self):
        while not self._ended:
            self._cond.acquire()
            self._cond.wait()
            items = self._queue[:]
            self._queue.clear()
            self._cond.release()
            for item in items:
                yield item

        items = self._queue[:]
        for item in items:
            yield item

class Producer(Thread, metaclass=ABCMeta):

    def __init__(self, endpoint):
        super(Producer, self).__init__()
        self._endpoint = endpoint

    @abstractmethod
    def _produce(self):
        pass

    def run(self):
        self._produce()

    def give(self, data):
        self._endpoint.give(data)

    def end(self):
        self.endpoint.end()

class Consumer(Thread, metaclass=ABCMeta):

    def __init__(self, endpoint):
        super(Consumer, self).__init__()
        self._endpoint = endpoint

    @abstractmethod
    def _consume(self):
        pass

    def run(self):
        self._consume()

    def take(self):
        return self._endpoint.take()

class GeneratorProducer(Producer):

    def __init__(self, endpoint, code):
        super(GeneratorProducer, self).__init__(endpoint)
        self._namespace = {}
        exec(code, self._namespace)

        def noop(*args, **kwargs):
            pass
        
        self._gen = self._namspace.get('gen', noop)

    def _produce(self):
        """ Simple generator style produce function
        """
        for item in self._gen():
            self.give(item)

        self.end()

class WebsocketServerConsumer(Consumer):

    def __init__(self, endpoint, port):
        super(WebsocketServerConsumer, self).__init__(endpoint)
        self._port = port

    def _consume(self):

        async def action(websocket, path):
            for msg in self.take():
                logger.debug(f'Received msg: {msg} from Producer, sending it to client')
                await websocket.send(msg)
                logger.debug(f'msg sent')
            logger.debug('exiting action, closing websocket server')
            self._server.close()

        async def start_action():
            async with websockets.serve(action, 'localhost', self._port) as server:
                self._sever = server
                await server.wait_closed()

        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(start_action())

class BacktestMachine(object):

    _producer_types = {
        'GENERATOR_MODE' : GeneratorProducer,
        # 'ZIPLINE_MODE' : ZiplineProducer
    }

    def __init__(self, code, mode='GENERATOR_MODE'):
        self._endp = Endpoint()
        self._port = getFreePort()
        self._producer = BacktestMachine._producer_types[mode](self._endp, code)
        self._consumer = WebsocketServerConsumer(self._endp, self._port)

    def getEndpoint(self):
        return self._port

    def start(self):
        self._producer.start()
        self._consumer.start()

    def stop(self):
        self._producer.stop()
        self._consumer.stop()
        self._producer.join()
        self._consumer.join()
