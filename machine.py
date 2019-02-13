"""High level abstraction of the logic of running a backtest - BacktestMachine
"""
# pylint: disable=C,R,I
from threading import Thread
from queue import Queue
import asyncio
import websockets
from abc import ABCMeta, abstractmethod
from util import getFreePort
import os
import logging
import sys
from zipline.utils.run_algo import _run
from trading_calendars import get_calendar
import pandas as pd

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

        logger.debug('code={}'.format(code))
        
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


class ZiplineProducer(Producer):

    def __init__(self, endpoint, code, start='2012-01-01', end='2018-12-01', capital_base=10000000):
        super(ZiplineProducer, self).__init__(endpoint)

        self._start = start
        self._end = end
        self._capital_base = capital_base

        spy_init_code = """
    import inspect
    stacks = inspect.stack()

    producer_proxy = None
    while stacks:
        stacks, stack = stacks[1:], stack[0]
        frame, filename, lineno, func, code_ctx, index = stack
        if stack.f_locals['producer_proxy']:
            producer_proxy = stack.f_locals['producer_proxy']
            break
    if producer_proxy == None:
        raise Error('Cannot find any stack that has producer_proxy')
    
    context.producer_proxy = producer_proxy
        """

        spy_action_code = """
    context.producer_proxy.send(context.portfolio)
        """

        code = code.split('\n')
        try:
            i = list(filter(lambda x: 'def initialize' in x[1], enumerate(code)))[0][0]
            code.insert(i + 1, spy_init_code)

            j = list(filter(lambda x: 'def handle_data' in x[1], enumerate(code)))[0][0]
            code.insert(j + 1, spy_action_code)

            self._algocode = '\n'.join(code)

            self._initSuccess = True
            
        except Exception as e:
            logger.error('Failed to failed <initialize> or <handle_data> in code')
            self._initSuccess = False

    def _produce(self):

        if not self._initSuccess:
            logger.info('Failed to initialize zipline producer, exiting..')
            return

        producer_proxy = self
        perf = _run(
            handle_data=None,
            initialize=None,
            before_trading_start=None,
            analyze=None,
            algofile='<string>',
            algotext=self._algocode,
            defines=(),
            data_frequency='daily',
            capital_base=self._capital_base,
            bundle='qunadl',
            bundle_timestamp=pd.Timestamp.utcnow(),
            start=self._start,
            end=self._end,
            output='-',
            trading_calendar=get_calendar('XNYS'),
            print_algo=False,
            metrics_set='default',
            local_namespace=None,
            environ=os.environ,
            blotter='default',
            benchmark_returns=None
        )

    def send(self, portfolio):

        if self._stopRequired:
            return

        self.give(portfolio.portfolio_value)
            

class WebsocketServerConsumer(Consumer):

    def __init__(self, endpoint, port):
        super(WebsocketServerConsumer, self).__init__(endpoint)
        self._port = port

    def _consume(self):

        async def action(websocket, path):
            if self._stopRequired:
                self._server.close()
                return

            logger.info('Waiting for client sending ready signal');
            
            ready = ''
            while ready != 'READY':
                ready = await websocket.recv()

            logger.info('Consumer receives ready signal.')
            
            for msg in self.take():
                
                logger.info('Received msg: {msg} from Producer, sending it to client')
                print('Websocket is in {}'.format(websocket.state))
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
        'ZIPLINE_MODE' : ZiplineProducer
    }

    def __init__(self, code, params={}, mode='GENERATOR_MODE'):
        self._endp = Endpoint()
        self._port = getFreePort()
        self._producer = BacktestMachine._producer_types[mode](self._endp, code, **params)
        self._consumer = WebsocketServerConsumer(self._endp, self._port)
        self._params = params

    def getEndpoint(self):
        return self._port

    def start(self):
        self._producer.start()
        self._consumer.start()

    def restart(self, newCode, newMode, params={}):
        if len(params) == 0:
            params = self._params
        self._producer = BacktestMachine._producer_types[newMode](self._endp, newCode, **params)
        self._consumer = WebsocketServerConsumer(self._endp, self._port)
        self.start()

    def stop(self):
        self._producer.stop()
        self._consumer.stop()
        self._producer.join()
        self._consumer.join()

    def stopped(self):
        return not self._producer.is_alive() and not self._consumer.is_alive()


if __name__ == '__main__':
    # python tin.py run zipline < algo.py | python tin.py -plot
    # tin run zipline < algo.py | tin -plot
    # tin run zipline -s 2012-01-01 -e 2018-12-12 < algo.py | tin plot
    #
    #
    #
    # nit run zipline algo1.py algo2.py algo3.py algo4.py -p
    #
    # import machine
    # import plotter
    # m = ZiplineMachine()
    # m.run('algo.py')
    # plotter.plot(m.output)
    #
    # run/liverun/maintain/show/dialog/livehost/dayrun/runasday/serve/runlive/run-live/
    # runday/exp/experiment/start/service/many/run-many/run-longterm/run-mini/run-persist/
    # run-live/run-real/run -realtime/service -realtime
    #
    # There's a difference between "run" and "service"
    #
    # >> run zipline ./algo.py
    # Starts another thread and direct the output to shell stdout
    # >> run zipline ./algo.py -plot
    # Starts another thread and direct the output to a http server which serves the plot, the http server automatically terminates after all data's sent
    #
    # >>
    #
    # >> help
    #    Commands:
    # clear       clear the screen
    # client      Prints the pool's current client
    # debug       Turn debug statements on or off
    # exit        exit the program
    # help        display help
    # miners      Prints the miner(s) connected to the pool


