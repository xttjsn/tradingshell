import os
from threading import Thread
import tornado.web
import json
import asyncio
import websockets
import traceback
import subprocess
from multiprocessing import Process
from enum import Enum
from util import getFreePort

WEBPORT = 9000


class DisplayType(Enum):
    WEB = 0
    PLT = 1


class PlotHandler(tornado.web.RequestHandler):
    """Handles HTTP request to /plot

    The only job that PlotHanlder does is to return the websocket port
    upon requested.

    """
    def initialize(self, appRef):
        self.appRef = appRef

    def get(self):
        self.write({'port': self.appRef.wsport})


class WebPlotter(Thread):
    def __init__(self, dataReader, wsport, initParams: dict):
        super(WebPlotter, self).__init__()
        self.dataReader = dataReader
        self.wsport = wsport
        self.initParams = initParams

    def run(self):
        async def action(websocket, path):
            """Runs a websocket protocol with a web front end

            There are three types of messages: Init, Update, and End.
            The server will send an Init message with all parameters
            describing the plot (e.g. title, xlabel). Then for each
            message that gets read from dataReader, send a json string
            with type Update.

            Args:
                websocket (websocket): The client websocket
                path (str): The path for the socket (unused)

            Returns:
                None
            """

            initMessage = self.initParams
            initMessage.update({'type': 'Init'})
            await websocket.send(json.dumps(initMessage))

            for msg in self.dataReader:
                try:
                    msg = msg.decode('utf8')
                    msg = json.loads(str(msg))
                    msg.update({'type': 'Update'})
                    await websocket.send(json.dumps(msg))
                except Exception as e:
                    print(e)
                    traceback.print_exc()

            endMessage = {'type': 'End'}
            await websocket.send(json.dumps(endMessage))

            print('exiting action, closing websocket server')
            self.server.close()

        async def start_action():
            async with websockets.serve(action, 'localhost', self.wsport)\
                       as server:
                self.server = server
                await server.wait_closed()

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(start_action())
        except websockets.exceptions.ConnectionClosed as e:
            print(e)
            os.exit(1)


class WebDisplayServer(tornado.web.Application):
    def __init__(self, dataReader, initParams: dict):
        """Initialize a web display server

        The web display server will create a free port used for
        interaction between the front end client and the web plotter.
        The web plotter will be run as a separate thread.

        Args:
            dataReader (object): An object that has implemented __iter__
                                 and __next__. __next__ should return a json 
                                 string of the data.
            initParams (dict): A dictionary of some intialization params for
            the plot.
        """

        handlers = [
            (r'/plot', PlotHandler, {'appRef': self})
        ]

        settings = {
            'xsrf_cookies': False,
            'debug': True
        }

        self.wsport = getFreePort()
        self.plotter = WebPlotter(dataReader, self.wsport, initParams)
        self.plotter.start()

        super(WebDisplayServer, self).__init__(handlers, **settings)


class WebDisplayServerProcess(Process):
    """Represents an individual process to run webdisplayserver

    It receives the same args as WebDisplayServer, only have other
    methods to start and stop.

    """
    def __init__(self, dataReader, initParams: dict, port):
        super(WebDisplayServerProcess, self).__init__()
        self.server = WebDisplayServer(dataReader, initParams)
        self.port = port

    def run(self):
        self.server.listen(self.port)
        tornado.ioloop.IOLoop.current().start()


class DisplayManager():
    def __init__(self):
        self.namedDisplay = {}

    def createPlot(self, name, displayType, dataSource, initParams):
        """Create the named plot of certain displayType

        For web display, start two processes. One for the web server,
        one for the front end webpack server. namedDisplay stores a
        tuple. The first element is a function to close the Plot. The
        second element is a tuple of display-specific variables like
        server process and client process.

        """
        if displayType == DisplayType.WEB:
            # if not isFreePort(WEBPORT):
            #     print('WEBPORT {} is not free yet.'.format(WEBPORT))
            #     return

            server = WebDisplayServerProcess(dataSource, initParams, WEBPORT)
            server.start()
            client = subprocess.Popen(['npm', 'start'], cwd='./display/web')

            def closePlot():
                if server.is_alive():
                    server.terminate()

                client.terminate()
                client.kill()

            self.namedDisplay[name] = (closePlot, (server, client))

        else:
            print('NOT YET IMPLEMENTED!')
            return

    def closePlot(self, name):
        closefunc, _ = self.namedDisplay[name]
        closefunc()
