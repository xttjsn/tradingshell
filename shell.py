"""The shell itself
"""
import os
import json
import argparse
import pdb
from base import (MyCmd,
                  with_argparser,
                  pipeReader,
                  MSG_SEP)
from service import WebDisplayService
from backtest import ZiplineRunThread
import time

DEFAULT_PLOT_NAME = '<default_plot>'


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
        self.services = {}

    def get_service(self, name):
        try:
            service = self.services[name]
        except Exception:
            service = WebDisplayService()
            self.services[name] = service
        return service

    def do_b(self, arg):
        self.do_backtest(arg)

    def do_backtest(self, arg):
        self.piperun('backtest ' + arg)

    argparser = argparse.ArgumentParser()
    argparser.add_argument('engine', default='zipline')
    argparser.add_argument('algofile', default='./algo.py')
    @with_argparser(argparser)
    def backtest(self, args, inPipe=None, outPipe=1):
        if args.engine not in self.backtest_engines:
            self.poutput('{} not a valid backtest engine'.format(args.engine))
            return

        with open(args.algofile, 'r') as f:
            code = f.read()

        r, w = os.pipe()

        def consume_portfolio(portfolio):
            update = json.dumps({
                'portfolio_value': portfolio['portfolio_value'],
                'pnl': portfolio['pnl'],
                'return': portfolio['returns']
            }).encode('utf8') + MSG_SEP
            os.write(outPipe, update)

        ziplineTh = ZiplineRunThread(code, '2012-01-01', '2012-6-01', 100000,
                                     consume_portfolio)
        ziplineTh.start()

    def do_p(self, arg):
        self.do_plot(arg)

    def do_plot(self, arg):
        pdb.set_trace()
        self.piperun('plot ' + arg)

    argparser = argparse.ArgumentParser()
    argparser.add_argument('frontend', default='web')
    @with_argparser(argparser)
    def plot(self, arg, inPipe=None, outPipe=1):
        """Plot the current data according to its type
        """

        if arg.frontend == 'web':
            service = self.get_service('webdisplay')

            if inPipe is not None:
                initParams = {
                    'title': 'Default Plot',
                    'xlabel': 'Date',
                    'startDate': '2012-01-01'
                }

                service.start()
                self.poutput('Waiting for service to start...')
                time.sleep(3)

                initParams = {
                    'title': 'Default Plot',
                    'xlabel': 'Date',
                    'startDate': '2012-01-01'
                }
                service.updateAddPlotter(pipeReader(inPipe, MSG_SEP),
                                         initParams)

            else:
                raise Exception('Non-pipe data model not implemented!')

        elif arg.frontend == 'plt':
            raise Exception('plt front end not implemented yet!')

    def do_s(self, arg):
        self.do_service(arg)

    def do_service(self, arg):
        self.piperun('service ' + arg)

    argparser = argparse.ArgumentParser()
    argparser.add_argument('service', default='webdisplay')
    argparser.add_argument('action', default='status')
    @with_argparser(argparser)
    def service(self, arg, inPipe=None, outPipe=1):
        """Manage services
        """
        # Run backtest as a service, once per day.
        # Make it manageable through this shell.
        # I.e. store the PID in database somewhere
        if arg.service == 'webdisplay':
            service = self.get_service('webdisplay')

            if arg.action == 'start':
                service.start()

            elif arg.action == 'status':
                self.poutput(service.status())

            elif arg.action == 'stop':
                service.stop()

            elif arg.action == 'update':
                if inPipe is None:
                    return

                initParams = {
                    'title': 'Default Plot',
                    'xlabel': 'Date',
                    'startDate': '2012-01-01'
                }
                service.updateAddPlotter(pipeReader(inPipe, MSG_SEP),
                                         initParams)

            else:
                self.perror('Invalid action {}.'.format(arg.action))

        else:
            self.perror('Not yet implemented: {}.'.format(arg.service))

    def do_db(self, arg):
        self.piperun('db ' + arg)

    def do_db_hello(self, arg):
        pass

    argparser = argparse.ArgumentParser()

    def db(self, arg, inPipe=None, outPipe=1):
        pass


if __name__ == '__main__':
    shell = TradingShell()
    shell.cmdloop()
