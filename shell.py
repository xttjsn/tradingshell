"""
The shell script
"""
import os
import sys
from cmd import Cmd


BLKSZ = 1024

class TradingShell(Cmd):

    prompt = '>>>'
    def __init__(self):
        super(TradingShell, self).__init__()
        self.backtest_engines = ['zipline']
        self.actions = {
            'backtest': self.backtest,
            'echo': self.echo
        }

    def piperun(self, arg):
        piped_args = arg.split('|')
        r = None
        for arg in piped_args:
            args = arg.split()
            if len(args) == 0:
                self.perror('Invalid args')
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

        self.writeTo(1, self.readFrom(r) + b'\n')
        
    def readFrom(self, pipe):
        # print('Reading from {}'.format(pipe))
        buf = b''
        while True and pipe:
            buf_more = os.read(pipe, BLKSZ)
            if not buf_more:
                break
            buf += buf_more

        # print("reading: {}".format(buf))
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
           
    def do_b(self, arg):
        self.do_backtest(arg)
        
    def do_backtest(self, arg):
        self.piperun('backtest ' + arg)

    def backtest(self, engine='zipline', algofile='./algo.py'):
        
        if args[0] not in self.backtest_engines:
            self.perror('{} not a valid backtest engine'.format(args[0]))
            return


        



if __name__ == '__main__':
    shell = TradingShell()
    shell.cmdloop()
