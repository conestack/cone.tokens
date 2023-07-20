from cone.sql import get_session
from cone.sql import testing as sql_testing
from cone.sql.testing import SQLLayer
from cone.tokens.browser.token import TokenAdd
from cone.tokens.browser.token import TokenAddForm
from cone.tokens.browser.token import TokenConsume
from cone.tokens.browser.token import TokenDelete
from cone.tokens.browser.token import TokenEdit
from cone.tokens.browser.token import TokenEditForm
from cone.tokens.exceptions import TokenLockTimeViolation
from cone.tokens.exceptions import TokenNotExists
from cone.tokens.exceptions import TokenTimeRangeViolation
from cone.tokens.exceptions import TokenUsageCountExceeded
from cone.tokens.model import TokenNode
from cone.tokens.model import TokenRecord
from cone.tokens.token import Tokens
from datetime import datetime 
from datetime import timedelta
from node.tests import NodeTestCase
from node.utils import UNSET
import sys
import unittest
import uuid


class TokensLayer(SQLLayer):

    def make_app(self):
        plugins = ['cone.tokens']
        kw = dict()
        kw['cone.plugins'] = '\n'.join(plugins)
        super().make_app(**kw)


tokens_layer = TokensLayer()


class TestTokens(NodeTestCase):
    layer = tokens_layer

    @sql_testing.delete_table_records(TokenRecord)
    def test_token_consume(self):
        request = self.layer.new_request()
        session = get_session(request)

        token = TokenRecord()
        uid = token.uid = uuid.uuid4()
        last_used = token.last_used = datetime(2023, 1, 1)
        token.valid_from = datetime.now()
        token.valid_to = datetime.now() + timedelta(1)
        token.lock_time = 0
        token.usage_count = 2
        session.add(token)

        token_api = Tokens(request)
        self.assertEqual(token_api.consume(uid), True)
        self.assertNotEqual(last_used, token.last_used)
        self.assertEqual(token.usage_count, 1)

        token.usage_count = 0
        session.commit()
        self.assertRaises(TokenUsageCountExceeded, token_api.consume, uid)

        token.usage_count = -1
        token.lock_time = 120
        session.commit()
        self.assertRaises(TokenLockTimeViolation, token_api.consume, uid)

        token.lock_time = 0
        token.valid_to = datetime(1999, 1, 1)
        session.commit()
        self.assertRaises(TokenTimeRangeViolation, token_api.consume, uid)

        token.valid_to = datetime.now() + timedelta(2)
        token.valid_from = datetime.now() + timedelta(1)
        session.commit()
        self.assertRaises(TokenTimeRangeViolation, token_api.consume, uid)

        session.delete(token)
        self.assertRaises(TokenNotExists, token_api.consume, uid)

    @sql_testing.delete_table_records(TokenRecord)
    def test_token_add(self):
        request = self.layer.new_request()
        session = get_session(request)

        token_api = Tokens(request)
        token_api.add(uuid.uuid4(), datetime.now() + timedelta(1), -1, 0)

        result = session.query(TokenRecord).one()
        self.assertEqual(isinstance(result, TokenRecord), True)

    @sql_testing.delete_table_records(TokenRecord)
    def test_token_delete(self):
        request = self.layer.new_request()
        session = get_session(request)

        token = TokenRecord()
        token.uid = uuid.uuid4()
        token.valid_from = datetime.now()
        token.valid_to = datetime.now() + timedelta(1)
        token.lock_time = 0
        token.usage_count = -1
        session.add(token)
        session.commit()

        token_api = Tokens(request)
        token_api.delete(token.uid)
        result = session.query(TokenRecord).all()
        self.assertEqual(result, [])

    @sql_testing.delete_table_records(TokenRecord)
    def test_token_update(self):
        request = self.layer.new_request()
        session = get_session(request)

        token = TokenRecord()
        token.uid = uuid.uuid4()
        token.valid_from = datetime.now()
        token.valid_to = datetime.now() + timedelta(1)
        token.lock_time = 0
        token.usage_count = -1
        session.add(token)
        session.commit()

        token_api = Tokens(request)
        token_api.update(
            token.uid,
            datetime(2022, 1, 1),
            datetime(2022, 1, 2),
            1,
            120
        )
        result = session.query(TokenRecord).one()
        self.assertEqual(isinstance(result, TokenRecord), True)
        self.assertEqual(result.valid_from,datetime(2022, 1, 1))
        self.assertEqual(result.valid_to,datetime(2022, 1, 2))
        self.assertEqual(result.lock_time, 120)
        self.assertEqual(result.usage_count, 1)

    @sql_testing.delete_table_records(TokenRecord)
    def test_token_addform(self):
        request = self.layer.new_request()

        # create token
        token = TokenNode()
        token.attrs['uid'] = uuid.uuid4()
        token.attrs['valid_from'] = datetime.now()
        token.attrs['valid_to'] = datetime.now() + timedelta(1)
        token.attrs['lock_time'] = 0
        token.attrs['usage_count'] = -1

        # prepare token form
        form_tile = TokenAddForm(None, 'render', 'addform')
        form_tile.model = token
        form_tile.request = request
        form_tile.action_resource = 'tokenform'
        form_tile.prepare()

        self.assertEqual(form_tile.form.name, 'tokenform')
        self.checkOutput("""
        <class 'yafowil.base.Widget'>: tokenform
        __<class 'yafowil.base.Widget'>: valid_from
        __<class 'yafowil.base.Widget'>: valid_to
        __<class 'yafowil.base.Widget'>: usage_count
        __<class 'yafowil.base.Widget'>: lock_time
        __<class 'yafowil.base.Widget'>: save
        __<class 'yafowil.base.Widget'>: cancel
        __<class 'yafowil.base.Widget'>: came_from
        __<class 'yafowil.base.Widget'>: factory
        """, form_tile.form.treerepr(prefix='_'))

        data = form_tile.form.extract(request=request)
        self.assertEqual(
            data.fetch('tokenform.valid_from').extracted,
            ''
        )
        self.assertEqual(
            data.fetch('tokenform.valid_to').extracted,
            UNSET
        )
        self.assertEqual(
            data.fetch('tokenform.usage_count').extracted,
            UNSET
        )
        self.assertEqual(
            data.fetch('tokenform.lock_time').extracted,
            UNSET
        )

        # save token
        request.params['tokenform.valid_from'] = datetime(2022, 1, 1)
        request.params['tokenform.valid_to'] = datetime(2022, 1, 2)
        request.params['tokenform.usage_count'] = -1
        request.params['tokenform.lock_time'] = 0
        request.params['action.tokenform.save'] = '1'
        form_tile(token, request)

        # check if data is saved
        self.assertEqual(token.attrs['valid_from'], datetime(2022, 1, 1))
        self.assertEqual(token.attrs['valid_to'], datetime(2022, 1, 2))
        self.assertEqual(token.attrs['usage_count'], -1)
        self.assertEqual(token.attrs['lock_time'], 0)

    @sql_testing.delete_table_records(TokenRecord)
    def test_token_editform(self):
        request = self.layer.new_request()

        # create token
        token = TokenNode()
        token.attrs['uid'] = uuid.uuid4()
        token.attrs['valid_from'] = datetime.now()
        token.attrs['valid_to'] = datetime.now() + timedelta(1)
        token.attrs['lock_time'] = 0
        token.attrs['usage_count'] = -1

        # prepare token form
        form_tile = TokenEditForm(None, 'render', 'editform')
        form_tile.model = token
        form_tile.request = request
        form_tile.action_resource = 'tokenform'
        form_tile.prepare()

        self.assertEqual(form_tile.form.name, 'tokenform')
        self.checkOutput("""    
        <class 'yafowil.base.Widget'>: tokenform
        __<class 'yafowil.base.Widget'>: valid_from
        __<class 'yafowil.base.Widget'>: valid_to
        __<class 'yafowil.base.Widget'>: usage_count
        __<class 'yafowil.base.Widget'>: lock_time
        __<class 'yafowil.base.Widget'>: save
        __<class 'yafowil.base.Widget'>: cancel
        __<class 'yafowil.base.Widget'>: came_from
        """, form_tile.form.treerepr(prefix='_'))

        data = form_tile.form.extract(request=request)
        self.assertEqual(
            data.fetch('tokenform.valid_from').extracted,
            ''
        )
        self.assertEqual(
            data.fetch('tokenform.valid_to').extracted,
            UNSET
        )
        self.assertEqual(
            data.fetch('tokenform.usage_count').extracted,
            UNSET
        )
        self.assertEqual(
            data.fetch('tokenform.lock_time').extracted,
            UNSET
        )

        # save token
        request.params['tokenform.valid_from'] = datetime(2022, 1, 1)
        request.params['tokenform.valid_to'] = datetime(2022, 1, 2)
        request.params['tokenform.usage_count'] = -1
        request.params['tokenform.lock_time'] = 0
        request.params['action.tokenform.save'] = '1'
        form_tile(token, request)

        # check if data is saved
        self.assertEqual(token.attrs['valid_from'], datetime(2022, 1, 1))
        self.assertEqual(token.attrs['valid_to'], datetime(2022, 1, 2))
        self.assertEqual(token.attrs['usage_count'], -1)
        self.assertEqual(token.attrs['lock_time'], 0)

    @sql_testing.delete_table_records(TokenRecord)
    def test_browser_jsonview_token(self):
        request = self.layer.new_request()
        token = TokenRecord()

        uid = request.params['uuid'] = uuid.uuid4()
        request.params['valid_from'] = datetime.now()
        request.params['valid_to'] = datetime.now() + timedelta(1)
        request.params['usage_count'] = -1
        request.params['lock_time'] = 1

        json_tile = TokenAdd(token, request)
        result = json_tile()
        self.assertEqual(result.json['token_uid'], str(uid))

        json_tile = TokenEdit(token, request)
        result = json_tile()
        self.assertEqual(result.json['token_uid'], str(uid))

        json_tile = TokenConsume(token, request)
        result = json_tile()
        self.assertEqual(result.json['consumed'], str(uid))

        json_tile = TokenDelete(token, request)
        result = json_tile()
        self.assertEqual(result.json['token_uid'], str(uid))


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
