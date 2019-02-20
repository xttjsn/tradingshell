import os
from threading import Thread
import tornado.web
import json
import asyncio
import websockets
import traceback
from util import getFreePort


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
                    print('Received msg: {msg} from Producer, sending it to client'
                          .format(msg=msg))
                    await websocket.send(json.dumps(msg))
                except Exception as e:
                    print(msg)
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
