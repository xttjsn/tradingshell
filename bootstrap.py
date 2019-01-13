import pymongo
import tornado.options
from tornado.options import define, options

import tbot_server 

define('user_email', default='tbot@tbot.com', help='email address for tbot user')
define('password', default='foobar', help='password for tbot user')

def bootstrap():
    tornado.options.parse_command_line()
    connection, db = tbot_server.connect_db()

    salt, encrypted_password = tbot_server.encrypt_password(None, options.password)

    if not db.users.find_one({'email' : options.user_email}):
        db.users.insert({'email' : options.user_email, 'encrypted_password' : encrypted_password, 'salt' : salt})


if __name__ == '__main__':
    bootstrap()
    
