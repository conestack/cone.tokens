from cone.app import get_root
from cone.sql import get_session
from cone.sql import testing as sql_testing
from cone.sql.testing import SQLLayer
from cone.tokens.browser.token import TokenAPIError
from cone.tokens.browser.token import TokenAddForm
from cone.tokens.browser.token import TokenEditForm
from cone.tokens.browser.token import TokenForm
from cone.tokens.browser.token import get_datetime
from cone.tokens.browser.token import get_int
from cone.tokens.exceptions import TokenLockTimeViolation
from cone.tokens.exceptions import TokenNotExists
from cone.tokens.exceptions import TokenTimeRangeViolation
from cone.tokens.exceptions import TokenUsageCountExceeded
from cone.tokens.model import TokenNode
from cone.tokens.model import TokenRecord
from cone.tokens.token import Tokens
from cone.ugm.testing import principals
from datetime import datetime 
from datetime import timedelta
from node.tests import NodeTestCase
from node.utils import UNSET
from pyramid.httpexceptions import HTTPForbidden
from pyramid.view import render_view_to_response
import sys
import unittest
import uuid


class TokensLayer(SQLLayer):

    def make_app(self):
        plugins = [
            'cone.ugm',
            'cone.sql',
            'cone.tokens'
        ]
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
        token_api.add(uuid.uuid4(),datetime.now(), datetime.now() + timedelta(1), -1, 0)

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

    def test_token_form(self):
        request = self.layer.new_request()

        # create token
        token = TokenNode()

        # prepare token form
        form_tile = TokenForm(attribute='render')
        form_tile.model = token
        form_tile.request = request
        form_tile.action_resource = 'tokenform'
        form_tile.prepare()

        # token form structure
        self.assertEqual(form_tile.form.name, 'tokenform')
        self.checkOutput("""
        <class 'yafowil.base.Widget'>: tokenform
        __<class 'yafowil.base.Widget'>: valid_from
        __<class 'yafowil.base.Widget'>: valid_to
        __<class 'yafowil.base.Widget'>: usage_count
        __<class 'yafowil.base.Widget'>: lock_time
        __<class 'yafowil.base.Widget'>: save
        __<class 'yafowil.base.Widget'>: cancel
        """, form_tile.form.treerepr(prefix='_'))

        # empty extraction
        data = form_tile.form.extract(request=request)
        self.assertEqual(data.fetch('tokenform.valid_from').extracted, '')
        self.assertEqual(data.fetch('tokenform.valid_to').extracted, UNSET)
        self.assertEqual(data.fetch('tokenform.usage_count').extracted, UNSET)
        self.assertEqual(data.fetch('tokenform.lock_time').extracted, UNSET)

        # extraction with values
        request.params['tokenform.valid_from'] = '1.1.2022'
        request.params['tokenform.valid_to'] = '2.1.2022'
        request.params['tokenform.usage_count'] = '-1'
        request.params['tokenform.lock_time'] = '0'
        request.params['action.tokenform.save'] = '1'
        data = form_tile.form.extract(request=request)
        self.assertEqual(
            data.fetch('tokenform.valid_from').extracted,
            datetime(2022, 1, 1, 0, 0)
        )
        self.assertEqual(
            data.fetch('tokenform.valid_to').extracted,
            datetime(2022, 1, 2, 0, 0)
        )
        self.assertEqual(data.fetch('tokenform.usage_count').extracted, -1.)
        self.assertEqual(data.fetch('tokenform.lock_time').extracted, 0)

    @principals(users={'admin': {}}, roles={'admin': ['manager']})
    @sql_testing.delete_table_records(TokenRecord)
    def test_token_addform(self):
        request = self.layer.new_request()

        # create token
        tokens = get_root()['tokens']
        token = TokenNode(parent=tokens)

        # prepare token form
        form_tile = TokenAddForm(attribute='render')
        form_tile.model = token
        form_tile.request = request
        form_tile.action_resource = 'tokenform'
        form_tile.prepare()

        # prepare request
        request.params['tokenform.valid_from'] = '1.1.2022'
        request.params['tokenform.valid_to'] = '2.1.2022'
        request.params['tokenform.usage_count'] = '-1'
        request.params['tokenform.lock_time'] = '0'
        request.params['action.tokenform.save'] = '1'

        # save token
        with self.layer.authenticated('admin'):
            form_tile(token, request)

        # check if token has been added
        self.assertEqual(len(tokens), 1)
        token = tokens.values()[0]
        self.assertEqual(token.attrs['valid_from'], datetime(2022, 1, 1))
        self.assertEqual(token.attrs['valid_to'], datetime(2022, 1, 2))
        self.assertEqual(token.attrs['usage_count'], -1)
        self.assertEqual(token.attrs['lock_time'], 0)

    @principals(users={'admin': {}}, roles={'admin': ['manager']})
    @sql_testing.delete_table_records(TokenRecord)
    def test_token_editform(self):
        request = self.layer.new_request()

        # create token
        tokens = get_root()['tokens']
        token_uid = str(uuid.uuid4())
        token = tokens[token_uid] = TokenNode()
        token.attrs['valid_from'] = datetime.now()
        token.attrs['valid_to'] = datetime.now() + timedelta(1)
        token.attrs['lock_time'] = 0
        token.attrs['usage_count'] = -1

        # prepare token form
        form_tile = TokenEditForm(attribute='render')
        form_tile.model = token
        form_tile.request = request
        form_tile.action_resource = 'tokenform'
        form_tile.prepare()

        # prepare request
        request.params['tokenform.valid_from'] = '1.1.2022'
        request.params['tokenform.valid_to'] = '2.1.2022'
        request.params['tokenform.usage_count'] = '-1'
        request.params['tokenform.lock_time'] = '0'
        request.params['action.tokenform.save'] = '1'

        # save token
        with self.layer.authenticated('admin'):
            form_tile(token, request)

        # check token has been edited
        self.assertEqual(token.attrs['valid_from'], datetime(2022, 1, 1))
        self.assertEqual(token.attrs['valid_to'], datetime(2022, 1, 2))
        self.assertEqual(token.attrs['usage_count'], -1)
        self.assertEqual(token.attrs['lock_time'], 0)

    @principals(users={'admin': {}}, roles={'admin': ['manager']})
    @sql_testing.delete_table_records(TokenRecord)
    def test_json_api(self):
        err = TokenAPIError('Error message')
        self.assertEqual(err.message, 'Error message')
        self.assertEqual(
            err.as_json(),
            dict(success=False, message='Error message')
        )

        request = self.layer.new_request()

        with self.assertRaises(TokenAPIError) as arc:
            get_datetime(request, 'dt')
        self.assertEqual(arc.exception.message, '`dt` missing on request')

        request.params['dt'] = 'invalid'
        with self.assertRaises(TokenAPIError) as arc:
            get_datetime(request, 'dt')
        self.assertEqual(arc.exception.message, 'Invalid datetime format')

        request.params['dt'] = datetime(2023, 7, 25, 7, 39).isoformat()
        self.assertEqual(
            get_datetime(request, 'dt'),
            datetime(2023, 7, 25, 7, 39)
        )

        del request.params['dt']
        self.assertIsInstance(
            get_datetime(request, 'dt', now_when_missing=True),
            datetime
        )

        with self.assertRaises(TokenAPIError) as arc:
            get_int(request, 'int')
        self.assertEqual(arc.exception.message, '`int` missing on request')

        request.params['int'] = 'invalid'
        with self.assertRaises(TokenAPIError) as arc:
            get_int(request, 'int')
        self.assertEqual(arc.exception.message, 'Value is no integer')

        request.params['int'] = '1'
        self.assertEqual(get_int(request, 'int'), 1)

    @principals(users={'admin': {}}, roles={'admin': ['manager']})
    @sql_testing.delete_table_records(TokenRecord)
    def test_json_api_add(self):
        tokens = get_root()['tokens']
        request = self.layer.new_request(type='json')
        request.method = 'POST'
        
        with self.assertRaises(HTTPForbidden) as arc:
            render_view_to_response(tokens, request, 'add_token')
        self.assertEqual(
            str(arc.exception),
            'Unauthorized: add_token failed permission check'
        )

        request.params['valid_from'] = datetime(2023, 7, 24, 8, 0).isoformat()
        request.params['valid_to'] = datetime(2023, 7, 25, 8, 0).isoformat()
        request.params['usage_count'] = '-1'
        request.params['lock_time'] = '1'
        with self.layer.authenticated('admin'):
            res = render_view_to_response(tokens, request, 'add_token')
        self.assertTrue(res.json['success'])

        request.params['valid_from'] = datetime(2023, 7, 25, 8, 0).isoformat()
        request.params['valid_to'] = datetime(2023, 7, 24, 8, 0).isoformat()
        request.params['usage_count'] = '-1'
        request.params['lock_time'] = '1'
        with self.layer.authenticated('admin'):
            res = render_view_to_response(tokens, request, 'add_token')
        self.assertFalse(res.json['success'])
        self.assertEqual(
            res.json['message'],
            'valid_from must be before valid_to'
        )

        del request.params['lock_time']
        with self.layer.authenticated('admin'):
            res = render_view_to_response(tokens, request, 'add_token')
        self.assertFalse(res.json['success'])
        self.assertEqual(
            res.json['message'],
            '`lock_time` missing on request'
        )

        del request.params['usage_count']
        with self.layer.authenticated('admin'):
            res = render_view_to_response(tokens, request, 'add_token')
        self.assertFalse(res.json['success'])
        self.assertEqual(
            res.json['message'],
            '`usage_count` missing on request'
        )

        del request.params['valid_to']
        with self.layer.authenticated('admin'):
            res = render_view_to_response(tokens, request, 'add_token')
        self.assertFalse(res.json['success'])
        self.assertEqual(
            res.json['message'],
            '`valid_to` missing on request'
        )

    @principals(users={'admin': {}}, roles={'admin': ['manager']})
    @sql_testing.delete_table_records(TokenRecord)
    def test_json_api_edit(self):
        request = self.layer.new_request(type='json')
        request.method = 'POST'
        token_api = Tokens(request)
        token_uid = uuid.uuid4()
        token_api.add(
            token_uid,
            datetime.now(),
            datetime.now() + timedelta(1),
            -1,
            0
        )
        tokens = get_root()['tokens']
        token = tokens[str(token_uid)]

        with self.assertRaises(HTTPForbidden) as arc:
            render_view_to_response(token, request, 'edit_token')
        self.assertEqual(
            str(arc.exception),
            'Unauthorized: edit_token failed permission check'
        )

        request.params['valid_from'] = datetime.now().isoformat()
        request.params['valid_to'] = (datetime.now() + timedelta(1)).isoformat()
        request.params['usage_count'] = '1'
        request.params['lock_time'] = '1'
        with self.layer.authenticated('admin'):
            res = render_view_to_response(token, request, 'edit_token')
        self.assertTrue(res.json['success'])
        self.assertEqual(token.attrs['usage_count'], 1)

        request.params['valid_from'] = datetime.now().isoformat()
        request.params['valid_to'] = (datetime.now() - timedelta(1)).isoformat()
        with self.layer.authenticated('admin'):
            res = render_view_to_response(token, request, 'edit_token')
        self.assertFalse(res.json['success'])
        self.assertEqual(
            res.json['message'],
            'valid_from must be before valid_to'
        )

        del request.params['lock_time']
        with self.layer.authenticated('admin'):
            res = render_view_to_response(token, request, 'edit_token')
        self.assertFalse(res.json['success'])
        self.assertEqual(
            res.json['message'],
            '`lock_time` missing on request'
        )

        del request.params['usage_count']
        with self.layer.authenticated('admin'):
            res = render_view_to_response(token, request, 'edit_token')
        self.assertFalse(res.json['success'])
        self.assertEqual(
            res.json['message'],
            '`usage_count` missing on request'
        )

        del request.params['valid_to']
        with self.layer.authenticated('admin'):
            res = render_view_to_response(token, request, 'edit_token')
        self.assertFalse(res.json['success'])
        self.assertEqual(
            res.json['message'],
            '`valid_to` missing on request'
        )

        del request.params['valid_from']
        with self.layer.authenticated('admin'):
            res = render_view_to_response(token, request, 'edit_token')
        self.assertFalse(res.json['success'])
        self.assertEqual(
            res.json['message'],
            '`valid_from` missing on request'
        )

        request.params['valid_from'] = datetime.now().isoformat()
        request.params['valid_to'] = (datetime.now() + timedelta(1)).isoformat()
        request.params['usage_count'] = '1'
        request.params['lock_time'] = '1'
        token_api.delete(token_uid)
        with self.layer.authenticated('admin'):
            res = render_view_to_response(token, request, 'edit_token')
        self.assertFalse(res.json['success'])
        self.assertEqual(
            res.json['message'],
            f'The token {token_uid} doesn\'t exists'
        )

    @principals(users={'admin': {}}, roles={'admin': ['manager']})
    @sql_testing.delete_table_records(TokenRecord)
    def test_json_api_delete(self):
        request = self.layer.new_request(type='json')
        request.method = 'POST'
        token_api = Tokens(request)
        token_uid = uuid.uuid4()
        token_api.add(
            token_uid,
            datetime.now(),
            datetime.now() + timedelta(1),
            -1,
            0
        )
        tokens = get_root()['tokens']
        token = tokens[str(token_uid)]

        with self.assertRaises(HTTPForbidden) as arc:
            render_view_to_response(token, request, 'delete_token')
        self.assertEqual(
            str(arc.exception),
            'Unauthorized: delete_token failed permission check'
        )

        with self.layer.authenticated('admin'):
            res = render_view_to_response(token, request, 'delete_token')
        self.assertTrue(res.json['success'])
        self.assertFalse(token_uid in tokens)

        with self.layer.authenticated('admin'):
            res = render_view_to_response(token, request, 'delete_token')
        self.assertFalse(res.json['success'])
        self.assertEqual(
            res.json['message'],
            f'The token {token_uid} doesn\'t exists'
        )

    @principals(users={'admin': {}}, roles={'admin': ['manager']})
    @sql_testing.delete_table_records(TokenRecord)
    def test_json_api_consume(self):
        request = self.layer.new_request(type='json')
        request.method = 'GET'
        token_api = Tokens(request)
        token_uid = uuid.uuid4()
        token_api.add(
            token_uid,
            datetime.now(),
            datetime.now() + timedelta(2),
            -1,
            0
        )
        tokens = get_root()['tokens']
        token = tokens[str(token_uid)]

        with self.assertRaises(HTTPForbidden) as arc:
            render_view_to_response(token, request, 'consume_token')
        self.assertEqual(
            str(arc.exception),
            'Unauthorized: consume_token failed permission check'
        )

        with self.layer.authenticated('admin'):
            res = render_view_to_response(token, request, 'consume_token')
        self.assertTrue(res.json['success'])
        self.assertTrue(res.json['consumed'])

        token.attrs['valid_from'] = datetime.now() + timedelta(1)
        with self.layer.authenticated('admin'):
            res = render_view_to_response(token, request, 'consume_token')
        self.assertFalse(res.json['success'])
        self.assertEqual(
            res.json['message'],
            f'The token {str(token_uid)} isn\'t in his valid Date Range'
        )

        token.attrs['lock_time'] = 10000000
        with self.layer.authenticated('admin'):
            res = render_view_to_response(token, request, 'consume_token')
        self.assertFalse(res.json['success'])
        self.assertEqual(
            res.json['message'],
            f'The token {str(token_uid)} has been recently used and is on cooldown'
        )

        token.attrs['usage_count'] = 0
        with self.layer.authenticated('admin'):
            res = render_view_to_response(token, request, 'consume_token')
        self.assertFalse(res.json['success'])
        self.assertEqual(
            res.json['message'],
            f'The token {str(token_uid)} has exceeded its durability'
        )

        del tokens[str(token_uid)]
        with self.layer.authenticated('admin'):
            res = render_view_to_response(token, request, 'consume_token')
        self.assertFalse(res.json['success'])
        self.assertEqual(
            res.json['message'],
            f'The token {token_uid} doesn\'t exists'
        )


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
