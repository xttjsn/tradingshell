import unittest
import os
import json
from base import MSG_SEP, pipeReader


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


class PipeTest(unittest.TestCase):
    """Test pipe-related functions and constructs
    """

    def testReader(self):
        r, w = os.pipe()

        # Send it to pipe, and keep every packet in a list
        sends = []
        for packet in fakeDataSource():
            os.write(w, packet + MSG_SEP)
            sends.append(packet)
        os.close(w)

        # Receive from pipe, and compare with packets in `sends`
        recvs = []
        source = pipeReader(r, MSG_SEP)
        for packet in source:
            recvs.append(packet)

        for s, r in zip(sends, recvs):
            self.assertTrue(s == r, "\ns[{}]={}\n\n r[{}]={}".format(sends.index(s),
                                                                s,
                                                                recvs.index(r),
                                                                r))
