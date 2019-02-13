"""Strategy
"""
# pylint: disable=C,R,I
import pathlib
import logging
import sys
import json

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
        if algoName is None:
            return ''

        logger.info('loading algo {}'.format(algoName))
        # DBEUG
        if algoName == 'testAlgo':
            return "print('Test code')"
        # End DEBUG


        path = pathlib.Path(__file__).parents[0].joinpath('static/algo/' + algoName + '.py')
        logger.info(path)
        try:
            strategy = Strategy(path=path)
            return strategy.code
        except Exception as e:
            logger.error('Exception happens while loading startegy {}: {}'.format(algoName, e))

    @staticmethod
    def loadAllStrategyNames():
        logger.info('loading all algo names')
        
        try:
            p = pathlib.Path(__file__).parents[0].joinpath('static/algo').glob('*.py')
            names = [f.parts[-1].split('.')[0] for f in p if f.is_file()]
            return {'StrategyNames': names}
        except Exception as e:
            logger.error('Exception happens while loading all strategy names: {}'.format(e))
            
