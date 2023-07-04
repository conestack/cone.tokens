import os
import sys
import unittest
import uuid
from cone.sql import get_session
from cone.sql import testing as sql_testing
from cone.sql.testing import SQLLayer
from node.tests import NodeTestCase
from cone.app.utils import add_creation_metadata
from cone.tokens.model import TokenNode
from cone.tokens.model import TokenRecord
from cone.tokens.token import Tokens
from datetime import datetime

class TokensLayer(SQLLayer):

    def make_app(self):
        plugins = ['cone.tokens']
        kw = dict()
        kw['cone.plugins'] = '\n'.join(plugins)
        os.environ['TESTRUN_MARKER'] = '1'
        super().make_app(**kw)


tokens_layer = TokensLayer()

@sql_testing.delete_table_records(TokenRecord)
class TestTokens(NodeTestCase):
    layer = tokens_layer

    def test_tokens(self):
        request = self.layer.new_request()
        session = get_session()
        token = TokenRecord()
        token.uid = uuid.uuid4(),
        token.last_used = datetime(2023,1,1)
        token.valid_from = datetime(2023,1,1)
        token.valid_to = datetime(2024,1,1)
        token.lock_time = 0
        session.add(token)




def run_tests():
    from cone.tokens import tests
    from zope.testrunner.runner import Runner

    suite = unittest.TestSuite()
    suite.addTest(unittest.findTestCases(tests))

    runner = Runner(found_suites=[suite])
    runner.run()
    sys.exit(int(runner.failed))


if __name__ == '__main__':
    run_tests()
