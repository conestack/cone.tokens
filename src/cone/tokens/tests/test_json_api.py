from cone.app import get_root
from cone.sql import testing as sql_testing
from cone.tokens.api import TokenAPI
from cone.tokens.browser.api import read_datetime
from cone.tokens.browser.api import read_int
from cone.tokens.browser.api import read_string
from cone.tokens.exceptions import TokenException
from cone.tokens.exceptions import TokenValueError
from cone.tokens.model import TokenRecord
from cone.tokens.model import TokenUsageRecord
from cone.tokens.settings import tokens_config
from cone.tokens.tests import tokens_layer
from cone.ugm import testing
from cone.ugm.testing import principals
from datetime import datetime 
from node.tests import NodeTestCase
from pyramid.httpexceptions import HTTPForbidden
from pyramid.view import render_view_to_response
from unittest.mock import patch
import os
import uuid


class TestJSONAPI(NodeTestCase):
    layer = tokens_layer

    def test_read_string(self):
        request = self.layer.new_request()
        kw = dict()

        read_string(request, 'param', kw)
        self.assertEqual(kw, dict())

        request.params['param'] = ''
        read_string(request, 'param', kw)
        self.assertEqual(kw, dict(param=None))

        read_string(request, 'param', kw, default='default')
        self.assertEqual(kw, dict(param='default'))

        request.params['param'] = 'value'
        read_string(request, 'param', kw)
        self.assertEqual(kw, dict(param='value'))

    def test_read_datetime(self):
        request = self.layer.new_request()
        kw = dict()

        read_datetime(request, 'param', kw)
        self.assertEqual(kw, dict())

        request.params['param'] = ''
        read_datetime(request, 'param', kw)
        self.assertEqual(kw, dict(param=None))

        read_datetime(request, 'param', kw, default=datetime(2023, 9, 22))
        self.assertEqual(kw, dict(param=datetime(2023, 9, 22)))

        with self.assertRaises(TokenValueError) as arc:
            request.params['param'] = 'foo'
            read_datetime(request, 'param', kw)
        self.assertEqual(arc.exception.message, 'param: invalid datetime format')

        request.params['param'] = datetime(2023, 9, 22, 10, 30).isoformat()
        read_datetime(request, 'param', kw)
        self.assertEqual(kw, dict(param=datetime(2023, 9, 22, 10, 30)))

    def test_read_int(self):
        request = self.layer.new_request()
        kw = dict()

        read_int(request, 'param', kw)
        self.assertEqual(kw, dict())

        request.params['param'] = ''
        read_int(request, 'param', kw)
        self.assertEqual(kw, dict(param=0))

        read_int(request, 'param', kw, default=-1)
        self.assertEqual(kw, dict(param=-1))

        with self.assertRaises(TokenValueError) as arc:
            request.params['param'] = 'foo'
            read_int(request, 'param', kw)
        self.assertEqual(arc.exception.message, 'param: value is no integer')

        request.params['param'] = '1'
        read_int(request, 'param', kw)
        self.assertEqual(kw, dict(param=1))

    @principals(users={'admin': {}}, roles={'admin': ['manager']})
    @sql_testing.delete_table_records(TokenRecord)
    def test_query_token(self):
        tokens = get_root()['tokens']
        request = self.layer.new_request(type='json')

        with self.assertRaises(HTTPForbidden) as arc:
            render_view_to_response(tokens, request, 'query_token')
        self.assertEqual(
            str(arc.exception),
            'Unauthorized: query_token failed permission check'
        )

        with self.layer.authenticated('admin'):
            res = render_view_to_response(tokens, request, 'query_token')
        self.assertFalse(res.json['success'])
        self.assertEqual(res.json['message'], 'Missing ``value`` parameter')

        request.params['value'] = 'token value'
        with patch.object(
            TokenAPI,
            'query_token',
            side_effect=Exception('Exception')
        ):
            with self.layer.authenticated('admin'):
                res = render_view_to_response(tokens, request, 'query_token')
            self.assertFalse(res.json['success'])
            self.assertEqual(res.json['message'], 'Exception')

        with self.layer.authenticated('admin'):
            res = render_view_to_response(tokens, request, 'query_token')
        self.assertTrue(res.json['success'])
        self.assertEqual(res.json['token'], None)

        token_api = TokenAPI(request)
        token_uid = uuid.uuid4()
        token_api.add(token_uid, value='token value')

        with self.layer.authenticated('admin'):
            res = render_view_to_response(tokens, request, 'query_token')
        self.assertTrue(res.json['success'])
        self.assertTrue(res.json['token'] is not None)
        self.assertEqual(res.json['token']['uid'], str(token_uid))

    @principals(users={'admin': {}}, roles={'admin': ['manager']})
    @sql_testing.delete_table_records(TokenRecord)
    @testing.temp_directory
    def test_add_token(self, tempdir):
        tokens_config.config_file = os.path.join(tempdir, 'tokens.json')
        tokens = get_root()['tokens']
        request = self.layer.new_request(type='json')
        request.method = 'POST'

        with self.assertRaises(HTTPForbidden) as arc:
            render_view_to_response(tokens, request, 'add_token')
        self.assertEqual(
            str(arc.exception),
            'Unauthorized: add_token failed permission check'
        )

        request.params['valid_from'] = 'foo'
        with self.layer.authenticated('admin'):
            res = render_view_to_response(tokens, request, 'add_token')
        self.assertFalse(res.json['success'])
        self.assertEqual(res.json['message'], 'valid_from: invalid datetime format')
        del request.params['valid_from']

        request.params['valid_to'] = 'foo'
        with self.layer.authenticated('admin'):
            res = render_view_to_response(tokens, request, 'add_token')
        self.assertFalse(res.json['success'])
        self.assertEqual(res.json['message'], 'valid_to: invalid datetime format')
        del request.params['valid_to']

        request.params['usage_count'] = 'foo'
        with self.layer.authenticated('admin'):
            res = render_view_to_response(tokens, request, 'add_token')
        self.assertFalse(res.json['success'])
        self.assertEqual(res.json['message'], 'usage_count: value is no integer')
        del request.params['usage_count']

        request.params['lock_time'] = 'foo'
        with self.layer.authenticated('admin'):
            res = render_view_to_response(tokens, request, 'add_token')
        self.assertFalse(res.json['success'])
        self.assertEqual(res.json['message'], 'lock_time: value is no integer')
        del request.params['lock_time']

        request.params['valid_from'] = datetime(2023, 9, 22).isoformat()
        request.params['valid_to'] = datetime(2023, 9, 21).isoformat()
        with self.layer.authenticated('admin'):
            res = render_view_to_response(tokens, request, 'add_token')
        self.assertFalse(res.json['success'])
        self.assertEqual(
            res.json['message'],
            'valid_from must be before valid_to'
        )
        del request.params['valid_from']
        del request.params['valid_to']

        with patch.object(
            TokenAPI,
            'add',
            side_effect=TokenException('TokenException')
        ):
            with self.layer.authenticated('admin'):
                res = render_view_to_response(tokens, request, 'add_token')
            self.assertFalse(res.json['success'])
            self.assertEqual(res.json['message'], 'TokenException')

        with patch.object(
            TokenAPI,
            'add',
            side_effect=Exception('Exception')
        ):
            with self.layer.authenticated('admin'):
                res = render_view_to_response(tokens, request, 'add_token')
            self.assertFalse(res.json['success'])
            self.assertEqual(res.json['message'], 'Exception')

        with self.layer.authenticated('admin'):
            res = render_view_to_response(tokens, request, 'add_token')
        self.assertTrue(res.json['success'])

        token_uid = res.json['token_uid']
        token = tokens[token_uid]
        self.assertEqual(token.attrs['value'], token_uid)
        self.assertEqual(token.attrs['valid_from'], None)
        self.assertEqual(token.attrs['valid_to'], None)
        self.assertEqual(token.attrs['usage_count'], 0)
        self.assertEqual(token.attrs['lock_time'], 0)

        request.params['value'] = ''
        request.params['valid_from'] = ''
        request.params['valid_to'] = ''
        request.params['usage_count'] = ''
        request.params['lock_time'] = ''
        with self.layer.authenticated('admin'):
            res = render_view_to_response(tokens, request, 'add_token')
        self.assertTrue(res.json['success'])

        token_uid = res.json['token_uid']
        token = tokens[token_uid]
        self.assertEqual(token.attrs['value'], token_uid)
        self.assertEqual(token.attrs['valid_from'], None)
        self.assertEqual(token.attrs['valid_to'], None)
        self.assertEqual(token.attrs['usage_count'], 0)
        self.assertEqual(token.attrs['lock_time'], 0)

        request.params['value'] = 'value'
        request.params['valid_from'] = datetime(2023, 9, 21).isoformat()
        request.params['valid_to'] = datetime(2023, 9, 22).isoformat()
        request.params['usage_count'] = '100'
        request.params['lock_time'] = '200'
        with self.layer.authenticated('admin'):
            res = render_view_to_response(tokens, request, 'add_token')
        self.assertTrue(res.json['success'])

        token_uid = res.json['token_uid']
        token = tokens[token_uid]
        self.assertEqual(token.attrs['value'], 'value')
        self.assertEqual(token.attrs['valid_from'], datetime(2023, 9, 21))
        self.assertEqual(token.attrs['valid_to'], datetime(2023, 9, 22))
        self.assertEqual(token.attrs['usage_count'], 100)
        self.assertEqual(token.attrs['lock_time'], 200)

    @principals(users={'admin': {}}, roles={'admin': ['manager']})
    @sql_testing.delete_table_records(TokenRecord)
    def test_update_token(self):
        request = self.layer.new_request(type='json')
        request.method = 'POST'

        token_api = TokenAPI(request)
        token_uid = uuid.uuid4()
        token_api.add(token_uid)

        tokens = get_root()['tokens']
        token = tokens[str(token_uid)]

        with self.assertRaises(HTTPForbidden) as arc:
            render_view_to_response(token, request, 'update_token')
        self.assertEqual(
            str(arc.exception),
            'Unauthorized: update_token failed permission check'
        )

        request.params['valid_from'] = 'foo'
        with self.layer.authenticated('admin'):
            res = render_view_to_response(token, request, 'update_token')
        self.assertFalse(res.json['success'])
        self.assertEqual(res.json['message'], 'valid_from: invalid datetime format')
        del request.params['valid_from']

        request.params['valid_to'] = 'foo'
        with self.layer.authenticated('admin'):
            res = render_view_to_response(token, request, 'update_token')
        self.assertFalse(res.json['success'])
        self.assertEqual(res.json['message'], 'valid_to: invalid datetime format')
        del request.params['valid_to']

        request.params['usage_count'] = 'foo'
        with self.layer.authenticated('admin'):
            res = render_view_to_response(token, request, 'update_token')
        self.assertFalse(res.json['success'])
        self.assertEqual(res.json['message'], 'usage_count: value is no integer')
        del request.params['usage_count']

        request.params['lock_time'] = 'foo'
        with self.layer.authenticated('admin'):
            res = render_view_to_response(token, request, 'update_token')
        self.assertFalse(res.json['success'])
        self.assertEqual(res.json['message'], 'lock_time: value is no integer')
        del request.params['lock_time']

        request.params['valid_from'] = datetime(2023, 9, 22).isoformat()
        request.params['valid_to'] = datetime(2023, 9, 21).isoformat()
        with self.layer.authenticated('admin'):
            res = render_view_to_response(token, request, 'update_token')
        self.assertFalse(res.json['success'])
        self.assertEqual(
            res.json['message'],
            'valid_from must be before valid_to'
        )
        del request.params['valid_from']
        del request.params['valid_to']

        with patch.object(
            TokenAPI,
            'update',
            side_effect=TokenException('TokenException')
        ):
            with self.layer.authenticated('admin'):
                res = render_view_to_response(token, request, 'update_token')
            self.assertFalse(res.json['success'])
            self.assertEqual(res.json['message'], 'TokenException')

        with patch.object(
            TokenAPI,
            'update',
            side_effect=Exception('Exception')
        ):
            with self.layer.authenticated('admin'):
                res = render_view_to_response(token, request, 'update_token')
            self.assertFalse(res.json['success'])
            self.assertEqual(res.json['message'], 'Exception')

        with self.layer.authenticated('admin'):
            res = render_view_to_response(token, request, 'update_token')
        self.assertTrue(res.json['success'])
        self.assertEqual(token.attrs['value'], str(token_uid))
        self.assertEqual(token.attrs['valid_from'], None)
        self.assertEqual(token.attrs['valid_to'], None)
        self.assertEqual(token.attrs['usage_count'], 0)
        self.assertEqual(token.attrs['lock_time'], 0)

        request.params['value'] = 'value'
        request.params['valid_from'] = datetime(2023, 9, 21).isoformat()
        request.params['valid_to'] = datetime(2023, 9, 22).isoformat()
        request.params['usage_count'] = '100'
        request.params['lock_time'] = '200'
        with self.layer.authenticated('admin'):
            res = render_view_to_response(token, request, 'update_token')
        self.assertTrue(res.json['success'])
        self.assertEqual(token.attrs['value'], 'value')
        self.assertEqual(token.attrs['valid_from'], datetime(2023, 9, 21))
        self.assertEqual(token.attrs['valid_to'], datetime(2023, 9, 22))
        self.assertEqual(token.attrs['usage_count'], 100)
        self.assertEqual(token.attrs['lock_time'], 200)

    @principals(users={'admin': {}}, roles={'admin': ['manager']})
    @sql_testing.delete_table_records(TokenRecord)
    def test_delete_token(self):
        request = self.layer.new_request(type='json')
        request.method = 'POST'

        token_api = TokenAPI(request)
        token_uid = uuid.uuid4()
        token_api.add(token_uid)

        tokens = get_root()['tokens']
        token = tokens[str(token_uid)]

        with self.assertRaises(HTTPForbidden) as arc:
            render_view_to_response(token, request, 'delete_token')
        self.assertEqual(
            str(arc.exception),
            'Unauthorized: delete_token failed permission check'
        )

        with patch.object(
            TokenAPI,
            'delete',
            side_effect=Exception('Exception')
        ):
            with self.layer.authenticated('admin'):
                res = render_view_to_response(token, request, 'delete_token')
            self.assertFalse(res.json['success'])
            self.assertEqual(res.json['message'], 'Exception')

        with self.layer.authenticated('admin'):
            res = render_view_to_response(token, request, 'delete_token')
        self.assertTrue(res.json['success'])
        self.assertEqual(tokens.values(), [])

    @principals(users={'admin': {}}, roles={'admin': ['manager']})
    @sql_testing.delete_table_records(TokenRecord)
    @sql_testing.delete_table_records(TokenUsageRecord)
    def test_consume_token(self):
        request = self.layer.new_request(type='json')
        request.method = 'GET'

        token_api = TokenAPI(request)
        token_uid = uuid.uuid4()
        token_api.add(token_uid)

        tokens = get_root()['tokens']
        token = tokens[str(token_uid)]

        with self.assertRaises(HTTPForbidden) as arc:
            render_view_to_response(token, request, 'consume_token')
        self.assertEqual(
            str(arc.exception),
            'Unauthorized: consume_token failed permission check'
        )

        with patch.object(
            TokenAPI,
            'consume',
            side_effect=TokenException('TokenException')
        ):
            with self.layer.authenticated('admin'):
                res = render_view_to_response(token, request, 'consume_token')
            self.assertFalse(res.json['success'])
            self.assertEqual(res.json['message'], 'TokenException')

        with patch.object(
            TokenAPI,
            'consume',
            side_effect=Exception('Exception')
        ):
            with self.layer.authenticated('admin'):
                res = render_view_to_response(token, request, 'consume_token')
            self.assertFalse(res.json['success'])
            self.assertEqual(res.json['message'], 'Exception')

        token.attrs['usage_count'] = -1
        with self.layer.authenticated('admin'):
            res = render_view_to_response(token, request, 'consume_token')
        self.assertTrue(res.json['success'])
        self.assertTrue(res.json['consumed'])

        token.attrs['usage_count'] = 0
        with self.layer.authenticated('admin'):
            res = render_view_to_response(token, request, 'consume_token')
        self.assertFalse(res.json['success'])
        self.assertEqual(
            res.json['message'],
            f'Token {str(token_uid)} usage count exceeded'
        )
