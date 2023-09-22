from cone.app import get_root
from cone.sql import testing as sql_testing
from cone.tokens.api import TokenAPI
from cone.tokens.browser.api import get_datetime
from cone.tokens.browser.api import get_int
from cone.tokens.browser.api import get_int
from cone.tokens.exceptions import TokenAPIError
from cone.tokens.model import TokenRecord
from cone.tokens.tests import tokens_layer
from cone.ugm.testing import principals
from datetime import datetime 
from datetime import timedelta
from node.tests import NodeTestCase
from pyramid.httpexceptions import HTTPForbidden
from pyramid.view import render_view_to_response
from unittest.mock import patch
import uuid


class TestJSONAPI(NodeTestCase):
    layer = tokens_layer

    @principals(users={'admin': {}}, roles={'admin': ['manager']})
    @sql_testing.delete_table_records(TokenRecord)
    def _test_json_api_common(self):
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
    def _test_json_api_add(self):
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

        with patch.object(TokenAPI, 'add', side_effect=KeyError('Error')):
            with self.layer.authenticated('admin'):
                res = render_view_to_response(tokens, request, 'add_token')
            self.assertFalse(res.json['success'])
            self.assertEqual(
                res.json['message'],
                "'Error'"
            )

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
    def _test_json_api_edit(self):
        request = self.layer.new_request(type='json')
        request.method = 'POST'
        token_api = TokenAPI(request)
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

        with patch.object(TokenAPI, 'update', side_effect=KeyError('Error')):
            with self.layer.authenticated('admin'):
                res = render_view_to_response(token, request, 'edit_token')
            self.assertFalse(res.json['success'])
            self.assertEqual(
                res.json['message'],
                "'Error'"
            )

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
    def _test_json_api_delete(self):
        request = self.layer.new_request(type='json')
        request.method = 'POST'
        token_api = TokenAPI(request)
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

        with patch.object(TokenAPI, 'delete', side_effect=KeyError('Error')):
            with self.layer.authenticated('admin'):
                res = render_view_to_response(token, request, 'delete_token')
            self.assertFalse(res.json['success'])
            self.assertEqual(
                res.json['message'],
                "'Error'"
            )

        with self.layer.authenticated('admin'):
            res = render_view_to_response(token, request, 'delete_token')
        self.assertFalse(res.json['success'])
        self.assertEqual(
            res.json['message'],
            f'The token {token_uid} doesn\'t exists'
        )

    @principals(users={'admin': {}}, roles={'admin': ['manager']})
    @sql_testing.delete_table_records(TokenRecord)
    def _test_json_api_consume(self):
        request = self.layer.new_request(type='json')
        request.method = 'GET'
        token_api = TokenAPI(request)
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

        with patch.object(TokenAPI, 'consume', side_effect=KeyError('Error')):
            with self.layer.authenticated('admin'):
                res = render_view_to_response(token, request, 'consume_token')
            self.assertFalse(res.json['success'])
            self.assertEqual(
                res.json['message'],
                "'Error'"
            )

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
