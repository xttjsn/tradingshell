import unittest
import subprocess
from shell import WebPlotter

class WebPlotterTest(unittest.TestCase):

    def testOpen(self):
        p = subprocess.Popen(['npm', 'start'], cwd='./display/web')
        plotter = WebPlotter()
