import unittest
import json
from displayserver import WebDisplayServer
from shell import DisplayManager, DisplayType
import time


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

    def testManage(self):
        manager = DisplayManager()
        initParams = {
            'title': 'Testing Random Series',
            'xlabel': 'Date',
            'startDate': '2012-01-01'
        }
        manager.createPlot('randomTest', DisplayType.WEB,
                           fakeDataSource(), initParams)
        for i in range(15):
            print('Closing plot in {}...'.format(i))
            time.sleep(1)
        manager.closePlot('randomTest')


if __name__ == '__main__':
    unittest.main()
