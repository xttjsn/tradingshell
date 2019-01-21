"""Represent a user session
"""

class Session(object):

    def __init__(self):
        self.current_code = None

    def updateAlgoCode(self, code):
        self.current_code = code
        return self

    def runBacktest(self):
        return self

