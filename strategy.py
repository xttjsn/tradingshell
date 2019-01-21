"""Strategy
"""
import pathlib
import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Strategy(object):
    """Represent a cross-library strategy
    """
    def __init__(self, code=None, path=None):
        if path:
            if isinstance(path, str):
                path = pathlib.Path(path)

            with path.open() as f:
                code = f.read()

            self.code = code
            self.path = path
                
        elif code:
            self.code = code
            self.path = None
            
        else:
            raise ValueError("Neither code nor path is given for strategy")


class StrategyLoader(object):
    """Responsible for loading strategy from file system
    """
    @staticmethod
    def loadStrategy(algoName=None, **kwargs):
        if algoName == None:
            return ''

        #### DBEUG
        if algoName == 'testAlgo':
            return "print('Test code')"
        #### End DEBUG


        path = pathlib.Path(__file__).parents[0].joinpath('static/algo/' + algoName + '.py')
        logger.info(path)
        try:
            strategy = Strategy(path=path)
            return strategy.code
        except Exception as e:
            logger.error(f'Exception happens while loading startegy {algoName}: {e}')
                
        
