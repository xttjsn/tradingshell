"""
The shell script
"""
import os
import sys
from cmd2 import Cmd

BLKSZ = 1024

class TradingShell(Cmd):

    prompt = '>>>'
    colors = 'Always'
    def __init__(self):
        super(TradingShell, self).__init__()
        self.backtest_engines = ['zipline']
        self.actions = {
            'backtest': self.backtest
        }

    def parse(self, line, command):
        # backtest zipline ./algo.py

    def do_any(self, arg):
        arg = arg.lstrip().rstrip()
        if arg == '':
            return

        piped_args = arg.split('|')

        rend = sys.stdin
        for arg in piped_args:
            args = arg.split()
            if len(args) == 0:
                self.perror('Invalid args. | with spaces, really?')
                return

            command = args[0]

            newrend, wend = os.pipe()
            try:
                output = self.actions[command](self.parse(arg[1:]),
                                               stdin=rend,
                                               stdout=wend)
                rend = newrend

            except Exception as e:
                self.perror(e)

        while True:
            buf = os.read(newrend, BLKSZ)
            self.poutput(buf.encode('uft-8'))

    def do_b(self, arg):
        self.do_backtest(arg)
        
    def do_backtest(self, arg):
        self.do_any('backtest ' + arg)

    def backtest(self, engine=zipline, algofile='./algo.py'):
        
        if args[0] not in self.backtest_engines:
            self.perror('{} not a valid backtest engine'.format(args[0]))
            return


        



if __name__ == '__main__':
    shell = TradingShell()
    shell.cmdloop()
