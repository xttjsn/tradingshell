import tornado.httpserver
import tornado.auth
import tornado.escape
from tornado.options import define, options
import tornado.web
import hashlib
import pymongo
import uuid
import base64
import os
import logging
import datetime
import json
import sys
from action import UnboundAction
from strategy import StrategyLoader
from machine import BacktestMachine
from util import hashAlgo, compose

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger('tbot')

define('port', default=9000, type=int)
define('mongodb_host', default='127.0.0.1', help='mongodb host ip address')
define('mongodb_port', default=27017, help='mongodb port', type=int)
define('mongodb_dbname', default='tbot', help='database name')
define('mongodb_admin', default='tbotadmin', help='database admin')
define('mongodb_password', default='tbot1234567890', help='database password')

HASH_ALGO = 'sha256'

def connect_db():
    connection = pymongo.MongoClient(options.mongodb_host, options.mongodb_port)
    db = connection[options.mongodb_dbname]
    db.authenticate(options.mongodb_admin, options.mongodb_password)
    return connection, db

def encrypt_password(salt, password):
    if salt == None:
        h1 = hashlib.new(HASH_ALGO)
        h1.update(str(datetime.datetime.utcnow()) + '--' + password)
        salt = h1.hexdigest()

    h2 = hashlib.new(HASH_ALGO)
    h2.update(salt + '--' + password)
    encrypted_password = h2.hexdigest()

    return salt, encrypted_password

class BaseHandler(tornado.web.RequestHandler):

    def __init__(self, *args, **kwargs):
        super(BaseHandler, self).__init__(*args, **kwargs)

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

    def post(self):
        pass

    def get(self):
        pass

    def options(self):
        logger.info('Received an OPTIONS request at {self.request.uri}')
        self.set_status(204)
        self.finish()

class APIHandler(BaseHandler):

    def __init__(self, *args, **kwargs):
        super(APIHandler, self).__init__(*args, **kwargs)
        self.actionMap = {
            'getAlgoCode' : UnboundAction(StrategyLoader.loadStrategy),
            'verifySubmit' : UnboundAction(lambda algoCode: hashAlgo(algoCode, 'SHA256')),
            'runBacktest' : UnboundAction(self.handleRunBacktest.__get__(self)),
            'newSession' : self._newSession,
            'getAllAlgo' : UnboundAction(StrategyLoader.loadAllStrategyNames)
        }
        self.keyMap = {
            'getAlgoCode' : ['algoName'],
            'verifySubmit' : ['algoCode'],
            'runBacktest' : ['session_id', 'algoCode', 'mode'],
            'newSession' : [],
            'getAllAlgo' : []
        }

    def initialize(self, machineGroup, newSession):
        self._machineGroup = machineGroup
        self._newSession = newSession

    def handleRunBacktest(self, session_id, algoCode, mode):
        # if there is already a backtest machine for the session,
        # stop the machine, and create a new machine
        logger.info('running handleBacktest')
        try:
            if session_id not in self._machineGroup:
                bm = BacktestMachine(algoCode, mode)
                self._machineGroup[session_id] = bm
                bm.start()
            else:
                bm = self._machineGroup[session_id]
                if not bm.stopped():
                    bm.stop()    
                bm.restart(algoCode, mode)
        except Exception as e:
            logger.error(f'Exceptino while handling runBacktest {e}')
            logger.error(f'session_id: {session_id}')
            logger.error(f'algoCode: {algoCode}')
            logger.error(f'mode: {mode}')
            return e.args[0]
            
        ws_port = bm.getEndpoint()
        logger.info(f"ws_port : {ws_port}")
        return str(ws_port)
    
    def get(self):
        logger.info('Recived a GET request')
        self.write("TBot only accepts POST request")

    def post(self):
        try:
            logger.info(f'Received a POST request at {self.request.uri}')
            endpoint = self.request.uri.split('/')[-1]
            logger.info(f'Endoint: {endpoint}')
            action = self.actionMap[endpoint]
            logger.info(f'body: {self.request.body}')
            json = tornado.escape.json_decode(self.request.body)

            try:
                args = {k : json[k] for k in self.keyMap[endpoint]}
            except KeyError as e:
                missingKey = e.args[0]
                self.write(f'Missing key: {missingKey}. Check the program')
                return

            self.write(action(**args))
            
        except Exception as e:
            logger.error(f'Exception happens while handling {endpoint}: {e}')

class TBotApplication(tornado.web.Application):
    def __init__(self):
        self._machineGroup = {}
        self._sessions = set(['1234567890']) # test session id
        
        handlers = [
            (r'/api/.*', APIHandler, {
                'machineGroup' : self._machineGroup,
                'newSession' : lambda : self.newSession.__get__(self)()
            } )
        ]

        settings = {
            'template_path' : os.path.join(os.path.dirname(__file__), 'templates'),
            'static_path' : os.path.join(os.path.dirname(__file__), 'static'),
            'xsrf_cookies' : False,
            'cookie_secret' : base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes),
            'login_url' : '/login',
            'debug' : True
        }

        super(TBotApplication, self).__init__(handlers, **settings)

    def newSession(self):
        newSessionId = base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes)
        self._sessions.add(newSessionId)
        logger.info(f'newSession: {newSessionId}')
        return newSessionId

def main():
    tornado.options.parse_command_line()

    httpserver = tornado.httpserver.HTTPServer(TBotApplication())
    httpserver.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
    
