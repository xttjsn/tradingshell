"""All about backtests
"""
import os
import threading
import pandas as pd
from queue import Queue
from zipline.utils.run_algo import _run
from zipline.utils.cli import Date
from trading_calendars import get_calendar


class Channel:
    def __init__(self, consumer):
        self.queue = Queue()
        self.consumer = consumer

    def give(self, item):
        self.queue.put(item)
        self.consumer(item)

    def take(self):
        return self.queue.get()


class ZiplineRunThread(threading.Thread):

    def __init__(self, code, start, end, capital_base=100000,
                 consume_portfolio=None):
        super(ZiplineRunThread, self).__init__()
        self.code = code
        self.start_date = Date(tz='utc', as_timestamp=True).parser(start)
        self.end_date = Date(tz='utc', as_timestamp=True).parser(end)
        self.capital_base = capital_base
        self.consume_portfolio = consume_portfolio

    def dummy_consume(self, portfolio):
        # Structure of portfolio 'capital_used', 'cash', 'cash_flow',
        # 'current_portfolio_weights', 'pnl', 'portfolio_value',
        # 'positions', 'positions_exposure', 'positions_value',
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
            i = list(filter(lambda x: 'def initialize' in x[1],
                            enumerate(code)))[0][0]
            code.insert(i + 1, spy_init_code)

            j = list(filter(lambda x: 'def handle_data' in x[1],
                            enumerate(code)))[0][0]
            code.insert(j + 1, spy_action_code)

            algotext = '\n'.join(code)

        except Exception as e:
            print('Failed to find <initialize> or <handle_data> in code')
            print(e)
            return

        __channel__ = Channel(consumer=self.consume_portfolio or
                              self.dummy_consume)

        print(algotext)

        algotext = algotext
        algofile = None
        define = ()
        data_frequency = 'daily'
        capital_base = 1000000
        bundle = 'quandl'
        bundle_timestamp = pd.Timestamp.utcnow()
        start = self.start_date
        end = self.end_date
        output = '-'
        trading_calendar = get_calendar('XNYS')
        print_algo = False
        metrics_set = 'default'
        local_namespace = {}
        blotter = 'default'

        _ = _run(
            initialize=None,
            handle_data=None,
            before_trading_start=None,
            analyze=None,
            algofile=algofile,
            algotext=algotext,
            defines=define,
            data_frequency=data_frequency,
            capital_base=capital_base,
            data=None,
            bundle=bundle,
            bundle_timestamp=bundle_timestamp,
            start=start,
            end=end,
            output=output,
            trading_calendar=trading_calendar,
            print_algo=print_algo,
            metrics_set=metrics_set,
            local_namespace=local_namespace,
            environ=os.environ,
            blotter=blotter,
        )
