import unittest
import subprocess
from shell import WebPlotter
from shell import ThreadManager

class ThreadManagerTest(unittest.TestCase):

    def testSpawn():
        def thr1():
            import time
            cnt = 0
            while cnt < 10000:
                print(cnt)
                cnt = cnt + cnt + 1
                time.sleep(1)

        def thr2():
            import random
            import string
            import time
            for _ in range(100):
                s = ''.join([random.choice(string.ascii_letters)
                             for __ in range(10)])
                print(s)
                time.sleep(0.8)

        manager = ThreadManager()
        manager.start('thr1', thr1)
        manager.start('thr2', thr2)
      
class WebPlotterTest(unittest.TestCase):

    def testOpen(self):
        p = subprocess.Popen(['npm', 'start'], cwd='./display/web')
        plotter = WebPlotter()

        
