import unittest
import tornado.ioloop
import subprocess
import json
from webdisplayserver import WebDisplayServer


def fakeDataSource():
    import random
    base = 100000
    for _ in range(100):
        portfolioValue = random.uniform(80000, 150000)
        pnl = portfolioValue - base
        returnVal = pnl / base
        yield json.dumps({
            'portfolioValue': portfolioValue,
            'pnl': pnl,
            'return': returnVal
        }).encode('utf8')


class WebPlotterTest(unittest.TestCase):

    def testOpen(self):
        p = subprocess.Popen(['npm', 'start'], cwd='./display/web')
        initParams = {
            'title': 'Testing Random Series',
            'xlabel': 'Date',
            'startDate': '2012-01-01'
        }
        server = WebDisplayServer(fakeDataSource(), initParams)
        server.listen(9000)
        tornado.ioloop.IOLoop.current().start()

if __name__ == '__main__':
    unittest.main()
