import argparse
from cmd2 import Cmd
import os
import colorama
import traceback
import pdb

BLKSZ = 1024
COMMAND_FUNC_PREFIX = 'do_'
MSG_SEP = b'\xab'


def with_argparser(argparser: argparse.ArgumentParser):
    """Decorater for cmd commands

    Split the command string by space and feeds it to our argparser.
    The result goes to the wrapped function

    Args:
        argparser : The argparser to use. Usually a class variable

    """
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
    """ Decorater to close the outPipe when you forgets
    """
    import functools

    @functools.wraps(func)
    def cmd_wrapper(instance, *args, inPipe=None, outPipe=1, **kwargs):
        func(instance, *args, inPipe=inPipe, outPipe=outPipe, **kwargs)
        try:
            os.close(outPipe)
        except OSError:
            pass
    return cmd_wrapper


class MyCmd(Cmd):
    """Base cmd class for trading shell

    Implements command pipe through os.pipe()
    """
    # def perror(self, arg):
    #     print(colorama.Fore.RED + str(arg) + colorama.Style.RESET_ALL)

    # def poutput(self, arg):
    #     print(str(arg))

    def piperun(self, arg):
        piped_args = arg.split('|')
        r = None

        # pdb.set_trace()
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
                self.perror(str(e))
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
        self.writeTo(outPipe, buf + arg.encode('utf-8'))
        os.close(outPipe)
        return

    def do_quit(self, arg):
        return True


def pipeReader(pipe, sep):
    """Creates a generator that reads data packs from pipe

    Read from pipe until reaching a separator
    """

    curBuf = b''
    dirtyBuf = b''
    while pipe:
        dirtyBuf += os.read(pipe, BLKSZ)
        if not dirtyBuf:
            break

        curBuf += dirtyBuf.split(sep)[0]
        occur = dirtyBuf.find(sep)
        dirtyBuf = dirtyBuf[(occur % len(dirtyBuf)) + 1:]
        if occur >= 0:
            yield curBuf
            curBuf = b''
