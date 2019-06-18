import unittest
import sys 
sys.path.append('..')
from src.query import QueryRunner

class TestGetFrontPage(unittest.TestCase):

    def test_query_runner(self):
        qr = QueryRunner()
        results = qr.get_front_page(1,1)
        assert len(results[ list(results.keys())[0] ][0]['dsc'])
