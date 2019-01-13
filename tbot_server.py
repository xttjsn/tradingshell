import tornado.httpserver
import tornado.auth
from tornado.options import define, options
import tornado.web
import hashlib
import pymongo
import uuid
import base64
import os
import logging
import datetime

logger = logging.getLogger('tbot')

define('port', default=8000, type=int)
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
    
class HomePageHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')

class SignUpHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('signup.html')

class LoginHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('login.html')

class SetupHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('setup.html')

class StrategyPickerHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('strategypicker.html')

class StrategyMixerHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('strategymixer.html')

class MonitorHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('monitor.html')

class BacktestHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('backtest.html')

class TBotApplication(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/', HomePageHandler),
            (r'/signup', SignUpHandler),
            (r'/login', LoginHandler),
            (r'/setup', SetupHandler),
            (r'/strategy_picker', StrategyPickerHandler),
            (r'/strategy_mixer', StrategyMixerHandler),
            (r'/monitor', MonitorHandler),
            (r'/backtest', BacktestHandler),
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


def main():
    tornado.options.parse_command_line()

    httpserver = tornado.httpserver.HTTPServer(TBotApplication())
    httpserver.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
    
