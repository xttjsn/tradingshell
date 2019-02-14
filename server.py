"""
The server
"""
import sys
import socket
import logging
import thread

HOST = ''
PORT = 49876

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Server:

    def __init__(self):
        self.clients = {}

    def start(self):
        self._server_sock = socket.socket()
        self._host = HOST
        self._port = PORT

        logger.info('Server started!\nWaiting for clients..')
        self._server_sock.bind((self._host, self._port))
        self._server_sock.listen(5)
        
        while True:
            client , addr = self._server_sock.accept()
            self.clients[addr] = client
            thread.start_new_thread(self.handle_new_client, (client, addr))


    def handle_new_client(self, client, addr):
        
