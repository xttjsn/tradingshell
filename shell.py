"""
The shell script
"""
import os
import sys
import _thread
from cmd2 import Cmd
import argparse
import colorama
import traceback
from queue import Queue
from zipline.utils.run_algo import _run
from zipline.utils.cli import Date
from trading_calendars import get_calendar
import pandas as pd

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

def zipline_run(code):
    spy_init_code = """
    import inspect
    stacks = inspect.stack()[1:]

    __channel = None
    print(stacks)
    while stacks:
        stacks, stack = stacks[1:], stacks[0]
        frame, filename, lineno, func, code_ctx, index = stack
        # print('===========Stack locals============')
        # print(frame.f_locals)
        if '__channel' in frame.f_locals:
            __channel = frame.f_locals['__channel']
            break
    if __channel is None:
        raise Exception('Cannot find any stack that has __channel')
    
    context.__channel = __channel
        """

    spy_action_code = """
    context.__channel.give(context.portfolio)
        """
    code = code.split('\n')
    try:
        i = list(filter(lambda x: 'def initialize' in x[1], enumerate(code)))[0][0]
        code.insert(i + 1, spy_init_code)

        j = list(filter(lambda x: 'def handle_data' in x[1], enumerate(code)))[0][0]
        code.insert(j + 1, spy_action_code)

        algocode = '\n'.join(code)

    except Exception as e:
        print('Failed to failed <initialize> or <handle_data> in code')
        return

    capital_base = 100000
    start = Date(tz='utc', as_timestamp=True).parser('2012-01-01')
    end = Date(tz='utc', as_timestamp=True).parser('2018-12-21')

    def consume(portfolio):
        print(portfolio)
    
    __channel = Channel(consumer=consume)
    perf = _run(
        handle_data=None,
        initialize=None,
        before_trading_start=None,
        analyze=None,
        algofile='<string>',
        algotext=algocode,
        defines=(),
        data_frequency='daily',
        capital_base=capital_base,
        bundle='quandl',
        bundle_timestamp=pd.Timestamp.utcnow(),
        start=start,
        end=end,
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
    
class TradingShell(MyCmd):

    prompt = '>>>'
    allow_redirection = False
    def __init__(self):
        super(TradingShell, self).__init__()
        self.backtest_engines = ['zipline']
        self.actions = {
            'backtest': self.backtest,
            'echo': self.echo
        }
    
    def do_b(self, arg):
        self.do_backtest(arg)
        
    def do_backtest(self, arg):
        self.piperun('backtest ' + arg)


    argparser = argparse.ArgumentParser()
    argparser.add_argument('engine', default='zipline')
    argparser.add_argument('algofile', default='./algo.py')

    @with_pipecloser
    @with_argparser(argparser)
    def backtest(self, args, inPipe=None, outPipe=1):
        if args.engine not in self.backtest_engines:
            self.poutput('{} not a valid backtest engine'.format(args.engine))
            return

        with open(args.algofile, 'r') as f:
            code = f.read()
            _thread.start_new_thread(zipline_run, (code,))
            

if __name__ == '__main__':
    shell = TradingShell()
    shell.cmdloop()
