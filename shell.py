"""
The shell script
"""
import os
import sys
import threading
from cmd2 import Cmd
import json
import argparse
import colorama
import traceback
import asyncio
import websockets
from queue import Queue
from zipline.utils.run_algo import _run
from zipline.utils.cli import Date
from trading_calendars import get_calendar
import pymongo
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

BLKSZ = 1024
COMMAND_FUNC_PREFIX = 'do_'

def with_argparser(argparser: argparse.ArgumentParser):
    import functools

    def arg_decorator(func):
        @functools.wraps(func)
        def cmd_wrapper(instance, cmdline, **kwargs):
            try:
                args, unknown = argparser.parse_known_args(cmdline.split())
            except SystemExit:
                return
            else:
                return func(instance, args, **kwargs)

        argparser.prog = func.__name__
        if argparser.description is None and func.__doc__:
            argparser.description = func.__doc__

        cmd_wrapper.__doc__ = argparser.description

        setattr(cmd_wrapper, 'argparser', argparser)

        return cmd_wrapper

    return arg_decorator

def with_pipecloser(func):
    """ Trying to close outPipe when function finishes
    """
    import functools

    @functools.wraps(func)
    def cmd_wrapper(instance, *args, inPipe=None, outPipe=1, **kwargs):
        func(instance, *args, inPipe=inPipe, outPipe=outPipe, **kwargs)
        try:
            os.close(outPipe)
        except OSError as e:
            pass
    return cmd_wrapper

class ZiplineRunThread(threading.Thread):

    def __init__(self, code, start, end, capital_base=100000, consume_portfolio=None):
        super(ZiplineRunThread, self).__init__()
        self.code = code
        self.start_date = Date(tz='utc', as_timestamp=True).parser(start)
        self.end_date = Date(tz='utc', as_timestamp=True).parser(end)
        self.capital_base = capital_base
        self.consume_portfolio = consume_portfolio

    def dummy_consume(self, portfolio):
        # Structure of portfolio
        # 'capital_used', 'cash', 'cash_flow', 'current_portfolio_weights', 'pnl',
        # 'portfolio_value', 'positions', 'positions_exposure', 'positions_value',
        # 'returns', 'start_date', 'starting_cash'
        pass
    
    def run(self):
        spy_init_code = """
    import inspect
    stacks = inspect.stack()[1:]

    __channel = None
    print(stacks)
    while stacks:
        stacks, stack = stacks[1:], stacks[0]
        frame, filename, lineno, func, code_ctx, index = stack
        print(frame.f_locals)
        if '__channel__' in frame.f_locals:
            __channel = frame.f_locals['__channel__']
            break
    if __channel is None:
        raise Exception('Cannot find any stack that has __channel')
    
    context.__channel = __channel
        """

        spy_action_code = """
    context.__channel.give(context.portfolio)
        """
        code = self.code.split('\n')
        try:
            i = list(filter(lambda x: 'def initialize' in x[1], enumerate(code)))[0][0]
            code.insert(i + 1, spy_init_code)

            j = list(filter(lambda x: 'def handle_data' in x[1], enumerate(code)))[0][0]
            code.insert(j + 1, spy_action_code)

            algocode = '\n'.join(code)

        except Exception as e:
            print('Failed to find <initialize> or <handle_data> in code')
            print(e)
            return

        __channel__  = Channel(consumer=self.consume_portfolio or self.dummy_consume)
        perf = _run(
            handle_data=None,
            initialize=None,
            before_trading_start=None,
            analyze=None,
            algofile='<string>',
            algotext=algocode,
            defines=(),
            data_frequency='daily',
            capital_base=self.capital_base,
            bundle='intrinio',
            bundle_timestamp=pd.Timestamp.utcnow(),
            start=self.start_date,
            end=self.end_date,
            output='-',
            trading_calendar=get_calendar('XNYS'),
            print_algo=False,
            metrics_set='default',
            local_namespace=None,
            environ=os.environ,
            blotter='default',
            benchmark_returns=None
        )

class MyCmd(Cmd):
    
    def perror(self, arg):
        print(colorama.Fore.RED + str(arg) + colorama.Style.RESET_ALL)

    def poutput(self, arg):
        print(str(arg))
    
    def piperun(self, arg):
        piped_args = arg.split('|')
        r = None
        for arg in piped_args:
            args = arg.split()
            if len(args) == 0:
                self.perror('Invalid args: {}'.format(args))
                return

            command = args[0]

            rr, w = os.pipe()
            try:
                self.actions[command](' '.join(args[1:]),
                                      inPipe=r,
                                      outPipe=w)
                r = rr

            except Exception as e:
                self.perror(e)
                tb = traceback.format_exc()
                print(tb)

        self.writeTo(1, self.readFrom(r))
        
    def readFrom(self, pipe):
        buf = b''
        while True and pipe:
            buf_more = os.read(pipe, BLKSZ)
            if not buf_more:
                break
            buf += buf_more

        return buf

    def writeTo(self, pipe, buf):
        os.write(pipe, buf)

    def do_echo(self, arg):
        self.piperun('echo ' + arg)

    def echo(self, arg, inPipe=None, outPipe=1):
        buf = self.readFrom(inPipe)    
        self.writeTo(outPipe, buf + arg.encode('utf-8') )
        os.close(outPipe)
        return

    def do_quit(self, arg):
        return True

class Channel:
    def __init__(self, consumer):
        self.queue = Queue()
        self.consumer = consumer

    def give(self, item):
        self.queue.put(item)
        self.consumer(item)

    def take(self):
        return self.queue.get()

class WebsocketSender():

    def __init__(self, port):
        self.port = port

    async def send(self, msg):
        await websocket
            
    
class TradingShell(MyCmd):

    prompt = '>>>'
    def __init__(self):
        super(TradingShell, self).__init__()
        self.backtest_engines = ['zipline']
        self.actions = {
            'backtest': self.backtest,
            'echo': self.echo,
            'plot': self.plot,
            'service': self.service,
            'db': self.db
        }
        self.dbManager = DBManager()
    
    def do_b(self, arg):
        self.do_backtest(arg)
        
    def do_backtest(self, arg):
        self.piperun('backtest ' + arg)

    def consume_portfolio(self, portfolio):
        update = json.dumps({
            'portfolio_value' : portfolio['portfolio_value'],
            'pnl' : portfolio['pnl']
        })
        self.writeTo(self.outPipe, update)

    argparser = argparse.ArgumentParser()
    argparser.add_argument('engine', default='zipline')
    argparser.add_argument('algofile', default='./algo.py')
    @with_pipecloser
    @with_argparser(argparser)
    def backtest(self, args, inPipe=None, outPipe=1):
        if args.engine not in self.backtest_engines:
            self.poutput('{} not a valid backtest engine'.format(args.engine))
            return

        self.outPipe = outPipe
        
        with open(args.algofile, 'r') as f:
            code = f.read()

        ziplineTh = ZiplineRunThread(code, '2012-01-01', '2018-12-01', 100000, self.consume_portfolio)
        ziplineTh.start()

    def do_p(self, arg):
        self.do_plot(arg)

    def do_plot(self, arg):
        self.piperun('plot ' + arg)


    argparser = argparse.ArgumentParser()
    argparser.add_argument('frontend', default='web')
    @with_argparser(argparser)
    def plot(self, arg, inPipe=None, outPipe=1):

        if arg.frontend == 'web':
            if inPipe != None:
                dataModel = PipeDataModel(inPipe)
            else:
                raise Exception('Non-pipe data model not implemented!')
            
            self.display = WebDisplay(dataModel)
        elif arg.frontend == 'plt':
            raise Exception('plt front end not implemented yet!')

    def do_s(self, arg):
        self.do_service(arg)

    def do_service(self, arg):
        self.piperun('service ' + arg)

    def service(self, arg, inPipe=None, outPipe=1):
        # Run backtest as a service, once per day.
        # Make it manageable through this shell.
        # I.e. store the PID in database somewhere
        pass

    def do_db(self, arg):
        self.piperun('db ' + arg)

    def do_db_hello(self, arg):
        pass

    argparser = argparse.ArgumentParser()
    def db(self, arg, inPipe=None, outPipe=1):
        pass

    
class WebPlotter():
    def plot(self, inPipe, outPipe=1):
        async def action(websocket, path):
            if self._stopRequired:
                self._server.close()
                return

            print('Waiting for client sending ready signal');
            
            ready = ''
            while ready != 'READY':
                ready = await websocket.recv()

            print('Consumer receives ready signal.')
            
            for msg in DataModel:
                
                print('Received msg: {msg} from Producer, sending it to client'.format(msg=msg))
                print('Websocket is in {}'.format(websocket.state))
                await websocket.send(str(msg))

            await websocket.send('end')
                
            finished = ''
            while finished != 'FINISHED':
                finished = await websocket.recv()

            print('exiting action, closing websocket server')
            self._server.close()

        async def start_action():
            async with websockets.serve(action, 'localhost', port) as server:
                await server.wait_closed()

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(start_action())
        except websockets.exceptions.ConnectionClosed as e:
            print(e)
            os.exit(1)

class DBManager():
    def __init__(self):
        self.client = MongoClient()
        self.db = client['tradingshell']
        self.services = db['services']

    def putService(self, pid, name, desc):
        self.services.insert_one({
            'pid': pid,
            'name': name,
            'desc': desc
        })

    def removeServiceByPID(self, pid):
        self.services.delete_one({'pid' : pid})

    def removeServiceByName(self, name):
        self.services.delete_one({'name' : name})

class DisplayManager():
    def __init__(self):
        self.webDisplay = subprocess.Popen(['npm', 'start'], cwd='./display/web')

    def init_plot(self, title):
        ts = Timestamp.now()
        portfolioInitMessage = DisplayInitMessage(title='New portfolio',
                                                  xlable='Date',
                                                  numseries=3)
        send(portfolioInitMessage)

    def init_plt(self, title):
        raise Exception('init_plt not yet implemented')
        
    def update_plot(self, msg, plotId):
        sendMsg(msg, plotId)


################################

        
#############################
        # 'capital_used', 'cash', 'cash_flow', 'current_portfolio_weights', 'pnl',
        # 'portfolio_value', 'positions', 'positions_exposure', 'positions_value',
        # 'returns', 'start_date', 'starting_cash'

DisplayInitMessage = namedtuple('DisplayInitMessage',
                                'title xlabel numseries')



PortfolioUpdateMessage = namedtuple('PortfolioUpdateMessage',
                                    'portfolio_value pnl returns')


if __name__ == '__main__':
    shell = TradingShell()
    shell.cmdloop()
