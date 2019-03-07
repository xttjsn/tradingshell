"""Service
"""
from abc import ABCMeta, abstractmethod
from enum import Enum
import subprocess
import datetime
import socket
from displayserver import WebDisplayServerProcess

WEBPORT = 9000

class Service(metaclass=ABCMeta):
    """The abstract class for a service
    """

    @abstractmethod
    def start(self, *args, **kwargs):
        pass

    @abstractmethod
    def stop(self, *args, **kwargs):
        pass

    @abstractmethod
    def status(self, *args, **kwargs):
        pass


class ServiceStatus(Enum):
    RUNNING = 0
    STOPPED = 1


class WebDisplayService(Service):
    """Service for web display
    """

    def __init__(self, name='webdisplay-0', desc='Web Display Service'):
        self.name = name
        self.desc = desc
        self.status = ServiceStatus.STOPPED

    def start(self):
        self.backp = WebDisplayServerProcess(WEBPORT)
        self.backp.start()
        self.frontp = subprocess.Popen(['npm', 'start'], cwd='./display/web',
                                       stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE)
        self.status = ServiceStatus.RUNNING
        self.start = datetime.datetime.now()
        self.host = socket.gethostname()

    def updateAddPlotter(self, dataSource, initParams):
        self.backp.addPlotter(dataSource, initParams)

    def stop(self):
        self.frontp.kill()
        self.backp.terminate()
        self.status = ServiceStatus.STOPPED

    def status(self):
        template = """
        {name} -- {desc}
        Status: {status} since {start-ts}; {duration} ago
        PIDs: Front PID ({fpid}), Backend PID ({bpid})
        """

        statusLine = 'Inactive (dead)' if self.status == ServiceStatus.STOPPED\
                     else 'Active (running)'
        startTS = self.start.strftime('%a %Y-%m-%d %H:%M:%S %Z;')
        deltaTS = str((datetime.datetime.now() - self.start))
        fpid = self.frontp.pid
        bpid = self.backp.pid

        return template.format(name=self.name,
                               desc=self.desc,
                               status=statusLine,
                               start=startTS,
                               duration=deltaTS,
                               fpid=fpid,
                               bpid=bpid)
