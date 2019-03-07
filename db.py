"""All about database
"""
from pymongo import MongoClient


class DBManager():
    def __init__(self):
        self.client = MongoClient()
        self.db = self.client['tradingshell']
        self.services = self.db['services']

    def putService(self, pid, name, desc):
        self.services.insert_one({
            'pid': pid,
            'name': name,
            'desc': desc
        })

    def removeServiceByPID(self, pid):
        self.services.delete_one({'pid': pid})

    def removeServiceByName(self, name):
        self.services.delete_one({'name': name})
