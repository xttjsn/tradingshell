"""High level abstraction of the logic of running a backtest - BacktestMachine
"""
from threading import Thread
from queue import Queue
import asyncio
import websockets
from abc import ABCMeta, abstractmethod
from util import getFreePort
import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)

END_TAG = '__END__'

class Endpoint(object):
    def __init__(self):
        self._queue = Queue(100)

    def give(self, data):
        self._queue.put(data)

    def end(self):
        self._queue.put(END_TAG)
    
    def take(self):
        while True:
            item = self._queue.get()
            if item == END_TAG:
                return END_TAG
            yield item

class Producer(Thread, metaclass=ABCMeta):

    def __init__(self, endpoint):
        super(Producer, self).__init__()
        self._endpoint = endpoint
        self._stopRequired = False

    @abstractmethod
    def _produce(self):
        pass

    def run(self):
        self._produce()

    def give(self, data):
        self._endpoint.give(data)

    def end(self):
        self._endpoint.end()

    def stop(self):
        self._stopRequired = True

class Consumer(Thread, metaclass=ABCMeta):

    def __init__(self, endpoint):
        super(Consumer, self).__init__()
        self._endpoint = endpoint
        self._stopRequired = False

    @abstractmethod
    def _consume(self):
        pass

    def run(self):
        self._consume()

    def take(self):
        return self._endpoint.take()

    def stop(self):
        self._stopRequired = True

class GeneratorProducer(Producer):

    def __init__(self, endpoint, code):
        super(GeneratorProducer, self).__init__(endpoint)
        self._namespace = {}
        exec(code, self._namespace)

        def noop(*args, **kwargs):
            pass

        logger.debug(f'code={code}')
        
        self._gen = self._namespace.get('gen', noop)

    def _produce(self):
        """ Simple generator style produce function
        """
        if self._stopRequired:
            return
        
        for item in self._gen():

            # TODO: do we need lock it?
            if self._stopRequired:
                return
            
            self.give(item)

            if self._stopRequired:
                return

        self.end()

class WebsocketServerConsumer(Consumer):

    def __init__(self, endpoint, port):
        super(WebsocketServerConsumer, self).__init__(endpoint)
        self._port = port

    def _consume(self):

        async def action(websocket, path):
            if self._stopRequired:
                self._server.close()
                return

            logger.info(f'Waiting for client sending ready signal');
            
            ready = ''
            while ready != 'READY':
                ready = await websocket.recv()

            logger.info(f'Consumer receives ready signal.')
            
            for msg in self.take():
                
                logger.info(f'Received msg: {msg} from Producer, sending it to client')
                print(f'Websocket is in {websocket.state}')
                await websocket.send(str(msg))

            await websocket.send('end')
                
            finished = ''
            while finished != 'FINISHED':
                finished = await websocket.recv()

            logger.info('exiting action, closing websocket server')
            self._server.close()

        async def start_action():
            async with websockets.serve(action, 'localhost', self._port) as server:
                self._server = server
                await server.wait_closed()

        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(start_action())
        except websockets.exceptions.ConnectionClosed as e:
            logger.info('Websocket closed abruptly by client')

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

    def restart(self, newCode, newMode):
        self._producer = BacktestMachine._producer_types[newMode](self._endp, newCode)
        self._consumer = WebsocketServerConsumer(self._endp, self._port)
        self.start()

    def stop(self):
        self._producer.stop()
        self._consumer.stop()
        self._producer.join()
        self._consumer.join()

    def stopped(self):
        return not self._producer.is_alive() and not self._consumer.is_alive()
