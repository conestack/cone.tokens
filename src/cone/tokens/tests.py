
from cone.sql import get_session
from cone.sql import testing as sql_testing
from cone.sql.testing import SQLLayer
from cone.tokens.exceptions import TokenLockTimeViolation
from cone.tokens.exceptions import TokenNotExists
from cone.tokens.exceptions import TokenTimeRangeViolation
from cone.tokens.exceptions import TokenUsageCountExceeded
from cone.tokens.model import TokenRecord
from cone.tokens.token import Tokens
from datetime import datetime 
from datetime import timedelta
from node.tests import NodeTestCase
import os
import sys
import unittest
import uuid
class TokensLayer(SQLLayer):

    def make_app(self):
        plugins = ['cone.tokens']
        kw = dict()
        kw['cone.plugins'] = '\n'.join(plugins)
        os.environ['TESTRUN_MARKER'] = '1'
        super().make_app(**kw)


tokens_layer = TokensLayer()

class TestTokens(NodeTestCase):
    layer = tokens_layer

    @sql_testing.delete_table_records(TokenRecord)
    def test_tokens(self):
        request = self.layer.new_request()
        session = get_session(request)
        token = TokenRecord()
        uid = token.uid = uuid.uuid4()
        last_used = token.last_used = datetime(2023,1,1)
        token.valid_from = datetime.now()
        token.valid_to = datetime.now() + timedelta(1)
        token.lock_time = 0
        token.usage_count = 2
        session.add(token)
        token_api = Tokens(request,uid)
        self.assertEqual(token_api(),True)
        self.assertNotEqual(last_used,token.last_used)
        self.assertEqual(token.usage_count,1)
        token.usage_count = 0
        session.commit()
        self.assertRaises(TokenUsageCountExceeded,token_api.__call__)
        token.usage_count = -1
        token.lock_time = 120
        session.commit()
        self.assertRaises(TokenLockTimeViolation,token_api.__call__)
        token.lock_time = 0
        token.valid_to = datetime(1999,1,1)
        session.commit()
        self.assertRaises(TokenTimeRangeViolation,token_api.__call__)
        token.valid_to = datetime.now() + timedelta(2)
        token.valid_from = datetime.now() + timedelta(1)
        session.commit()
        self.assertRaises(TokenTimeRangeViolation,token_api.__call__)
        session.delete(token)
        self.assertRaises(TokenNotExists,token_api.__call__)



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
