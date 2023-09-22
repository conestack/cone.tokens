from cone.app import get_root
from cone.sql import get_session
from cone.sql import testing as sql_testing
from cone.sql.testing import SQLLayer
from cone.tokens.api import TokenAPI
from cone.tokens.browser.api import get_datetime
from cone.tokens.browser.api import get_int
from cone.tokens.browser.api import get_int
from cone.tokens.browser.token import TokenAddForm
from cone.tokens.browser.token import TokenContent
from cone.tokens.browser.token import TokenEditForm
from cone.tokens.browser.token import TokenForm
from cone.tokens.browser.token import b64_qr_code
from cone.tokens.browser.token import qr_code
from cone.tokens.browser.tokens import TokensContent
from cone.tokens.exceptions import TokenAPIError
from cone.tokens.exceptions import TokenLockTimeViolation
from cone.tokens.exceptions import TokenNotExists
from cone.tokens.exceptions import TokenTimeRangeViolation
from cone.tokens.exceptions import TokenUsageCountExceeded
from cone.tokens.exceptions import TokenValueError
from cone.tokens.model import TokenContainer
from cone.tokens.model import TokenNode
from cone.tokens.model import TokenRecord
from cone.ugm.testing import principals
from datetime import datetime 
from datetime import timedelta
from node.tests import NodeTestCase
from node.utils import UNSET
from pyramid.httpexceptions import HTTPForbidden
from pyramid.view import render_view_to_response
from unittest.mock import patch
from yafowil.base import ExtractionError
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


class TestModel(NodeTestCase):
    layer = tokens_layer

    @sql_testing.delete_table_records(TokenRecord)
    def test_TokenContainer(self):
        tokens = get_root()['tokens']

        self.assertEqual(tokens.record_class, TokenRecord)
        self.assertEqual(tokens.child_factory, TokenNode)
        self.assertEqual(
            tokens.uuid,
            uuid.UUID('c40ef458-832f-42e6-9add-2dda2afb8920')
        )

        self.assertEqual(tokens.metadata.title, 'token_container_title')
        self.assertEqual(
            tokens.metadata.description,
            'token_container_description'
        )

        self.assertTrue(tokens.properties.in_navtree)
        self.assertTrue(tokens.properties.action_up)
        self.assertTrue(tokens.properties.action_sharing)
        self.assertTrue(tokens.properties.action_view)
        self.assertTrue(tokens.properties.action_list)

    @sql_testing.delete_table_records(TokenRecord)
    def test_TokenNode(self):
        tokens = get_root()['tokens']
        self.assertEqual(isinstance(tokens, TokenContainer), True)

        # add token to tokens container
        token = TokenNode()
        token.attrs['value'] = 'value'
        token.attrs['valid_from'] = datetime(2023, 9, 21)
        token.attrs['valid_to'] = datetime(2023, 9, 22)
        token.attrs['lock_time'] = 0
        token.attrs['usage_count'] = -1
        token.attrs['creator'] = 'admin'
        token.attrs['created'] = datetime(2023, 9, 21)
        token.attrs['modified'] = datetime(2023, 9, 21)

        token_uuid = str(uuid.uuid4())
        tokens[token_uuid] = token
        token()

        # check if token has been added
        self.assertEqual(len(tokens), 1)
        token = tokens.values()[0]
        self.assertTrue(isinstance(token, TokenNode))
        self.assertEqual(token.attrs['value'], 'value')
        self.assertEqual(token.attrs['valid_from'], datetime(2023, 9, 21))
        self.assertEqual(token.attrs['valid_to'], datetime(2023, 9, 22))
        self.assertEqual(token.attrs['lock_time'], 0)
        self.assertEqual(token.attrs['usage_count'], -1)
        self.assertEqual(token.attrs['creator'], 'admin')
        self.assertEqual(token.attrs['created'], datetime(2023, 9, 21))
        self.assertEqual(token.attrs['modified'], datetime(2023, 9, 21))

        # check metadata
        self.assertEqual(token.metadata.title, 'value')
        self.assertEqual(token.metadata.creator, 'admin')
        self.assertEqual(token.metadata.created, datetime(2023, 9, 21))
        self.assertEqual(token.metadata.modified, datetime(2023, 9, 21))

        # check properties
        self.assertTrue(token.properties.action_up)
        self.assertEqual(token.properties.action_up_tile, 'content')
        self.assertTrue(token.properties.action_edit)
        self.assertTrue(token.properties.action_view)


class TestTokenAPI(NodeTestCase):
    layer = tokens_layer

    @sql_testing.delete_table_records(TokenRecord)
    def test__get_token(self):
        request = self.layer.new_request()
        session = get_session(request)

        token = TokenRecord()
        token_uid = token.uid = uuid.uuid4()

        session.add(token)
        session.commit()

        api = TokenAPI(request)
        self.assertEqual(api._get_token(token_uid).uid, token_uid)

        invalid_uid = uuid.UUID('f9c98a6b-b773-4714-b965-98c7911e6236')
        with self.assertRaises(TokenNotExists) as arc:
            api._get_token(invalid_uid)
        self.assertEqual(
            str(arc.exception),
            'Token f9c98a6b-b773-4714-b965-98c7911e6236 not exists'
        )

    @sql_testing.delete_table_records(TokenRecord)
    def test__query_token(self):
        request = self.layer.new_request()
        session = get_session(request)

        token = TokenRecord()
        token_uid = token.uid = uuid.uuid4()
        token_value = token.value = 'token value'

        session.add(token)
        session.commit()

        api = TokenAPI(request)
        self.assertEqual(api._query_token(''), None)
        self.assertEqual(api._query_token(token_value).uid, token_uid)

    @sql_testing.delete_table_records(TokenRecord)
    def test_consume(self):
        request = self.layer.new_request()
        session = get_session(request)

        token = TokenRecord()
        token_uid = uuid.UUID('577989d4-1673-4639-a579-dd468b294713')
        token.uid = token_uid
        token.value = 'token value'
        last_used = token.last_used = datetime(2023, 1, 1)
        token.valid_from = None
        token.valid_to = None
        token.lock_time = 0
        token.usage_count = -1
        session.add(token)

        api = TokenAPI(request)
        self.assertTrue(api.consume(token_uid))
        self.assertNotEqual(last_used, token.last_used)
        self.assertEqual(token.usage_count, -1)

        token.usage_count = 1
        session.commit()
        self.assertTrue(api.consume(token_uid))
        self.assertEqual(token.usage_count, 0)

        with self.assertRaises(TokenUsageCountExceeded) as arc:
            api.consume(token_uid)
        self.assertEqual(
            str(arc.exception),
            'Token 577989d4-1673-4639-a579-dd468b294713 usage count exceeded'
        )

        token.usage_count = -1
        token.lock_time = 120
        session.commit()
        with self.assertRaises(TokenLockTimeViolation) as arc:
            api.consume(token_uid)
        self.assertEqual(
            str(arc.exception),
            'Token 577989d4-1673-4639-a579-dd468b294713 is locked'
        )

        token.lock_time = 0
        session.commit()
        self.assertTrue(api.consume(token_uid))

        token.valid_from = datetime.now() + timedelta(days=1)
        session.commit()
        with self.assertRaises(TokenTimeRangeViolation) as arc:
            api.consume(token_uid)
        self.assertEqual(
            str(arc.exception),
            'Token 577989d4-1673-4639-a579-dd468b294713 out of time range'
        )

        token.valid_from = None
        token.valid_to = datetime.now() - timedelta(days=1)
        session.commit()
        with self.assertRaises(TokenTimeRangeViolation) as arc:
            api.consume(token_uid)
        self.assertEqual(
            str(arc.exception),
            'Token 577989d4-1673-4639-a579-dd468b294713 out of time range'
        )

        token.valid_from = datetime.now() - timedelta(days=1)
        token.valid_to = datetime.now() + timedelta(days=1)
        session.commit()

        self.assertTrue(api.consume(token_uid))

        session.delete(token)
        with self.assertRaises(TokenNotExists) as arc:
            api.consume(token_uid)
        self.assertEqual(
            str(arc.exception),
            'Token 577989d4-1673-4639-a579-dd468b294713 not exists'
        )

    @sql_testing.delete_table_records(TokenRecord)
    def test_add(self):
        request = self.layer.new_request()
        api = TokenAPI(request)
        token_uid = uuid.UUID('c27b6d86-8ac0-4261-9e62-151ff7e31ecb')
        api.add(token_uid)

        token = api._get_token(token_uid)
        self.assertEqual(token.value, str(token_uid))
        self.assertEqual(token.valid_from, None)
        self.assertEqual(token.valid_to, None)
        self.assertEqual(token.usage_count, -1)
        self.assertEqual(token.lock_time, 0)

        token_uid = uuid.UUID('6556f43e-b0ce-4c14-a0c5-40b8f2cdab3a')
        api.add(
            token_uid,
            value='token value',
            valid_from=datetime(2023, 9, 21),
            valid_to=datetime(2023, 9, 22),
            usage_count=0,
            lock_time=10
        )
        token = api._get_token(token_uid)
        self.assertEqual(token.value, 'token value')
        self.assertEqual(token.valid_from, datetime(2023, 9, 21))
        self.assertEqual(token.valid_to, datetime(2023, 9, 22))
        self.assertEqual(token.usage_count, 0)
        self.assertEqual(token.lock_time, 10)

        with self.assertRaises(TokenValueError) as arc:
            api.add(
                token_uid,
                valid_from=datetime(2023, 9, 21),
                valid_to=datetime(2023, 9, 21),
            )
        self.assertEqual(
            str(arc.exception),
            'Token with uid 6556f43e-b0ce-4c14-a0c5-40b8f2cdab3a already exists'
        )

        token_uid = uuid.UUID('9c9196f0-8b5b-42e7-b389-b13b267c9378')
        with self.assertRaises(TokenValueError) as arc:
            api.add(
                token_uid,
                valid_from=datetime(2023, 9, 21),
                valid_to=datetime(2023, 9, 21),
            )
        self.assertEqual(
            str(arc.exception),
            'valid_from must be before valid_to'
        )

    @sql_testing.delete_table_records(TokenRecord)
    def test_delete(self):
        request = self.layer.new_request()
        session = get_session(request)

        token = TokenRecord()
        token_uid = token.uid = uuid.UUID('cc3ebacb-1fc1-42ea-bc24-051b60d60545')
        session.add(token)
        session.commit()

        api = TokenAPI(request)
        api.delete(token_uid)
        with self.assertRaises(TokenNotExists) as arc:
            api.delete(token_uid)
        self.assertEqual(
            str(arc.exception),
            'Token cc3ebacb-1fc1-42ea-bc24-051b60d60545 not exists'
        )

    @sql_testing.delete_table_records(TokenRecord)
    def test_update(self):
        request = self.layer.new_request()
        session = get_session(request)

        token = TokenRecord()
        token_uid = token.uid = uuid.UUID('17b04001-4f42-4061-ad85-72de9ed8e287')
        token.value = 'value'
        session.add(token)

        token = TokenRecord()
        token.uid = uuid.UUID('c32e818c-af0c-4ee4-a855-0e50cad09e13')
        token.value = 'other value'
        session.add(token)
        session.commit()

        api = TokenAPI(request)
        with self.assertRaises(TokenValueError) as arc:
            api.update(token_uid, value='other value')
        self.assertEqual(
            str(arc.exception),
            'Given value already used by another token'
        )

        with self.assertRaises(TokenValueError) as arc:
            api.update(
                token_uid,
                valid_from=datetime(2023, 9, 21),
                valid_to=datetime(2023, 9, 21)
            )
        self.assertEqual(
            str(arc.exception),
            'valid_from must be before valid_to'
        )

        api.update(
            token_uid,
            value='new value',
            valid_from=datetime(2023, 9, 21),
            valid_to=datetime(2023, 9, 22),
            usage_count=10,
            lock_time=100
        )
        token = session\
            .query(TokenRecord)\
            .filter(TokenRecord.uid == token_uid)\
            .one()

        self.assertEqual(token.value, 'new value')
        self.assertEqual(token.valid_from, datetime(2023, 9, 21))
        self.assertEqual(token.valid_to, datetime(2023, 9, 22))
        self.assertEqual(token.usage_count, 10)
        self.assertEqual(token.lock_time, 100)


class TestTokenForms(NodeTestCase):
    layer = tokens_layer

    def test_TokenForm(self):
        request = self.layer.new_request()

        # create token
        token = TokenNode()

        class TestTokenForm(TokenForm):
            def next(self, request):
                ...

        # prepare token form
        form_tile = TestTokenForm(attribute='render')
        form_tile.model = token
        form_tile.request = request
        form_tile.action_resource = 'tokenform'
        form_tile.prepare()

        # token form structure
        self.assertEqual(form_tile.form.name, 'tokenform')
        self.checkOutput("""
        <class 'yafowil.base.Widget'>: tokenform
        __<class 'yafowil.base.Widget'>: value
        __<class 'yafowil.base.Widget'>: valid_from
        __<class 'yafowil.base.Widget'>: valid_to
        __<class 'yafowil.base.Widget'>: usage_count
        __<class 'yafowil.base.Widget'>: lock_time
        __<class 'yafowil.base.Widget'>: save
        __<class 'yafowil.base.Widget'>: cancel
        """, form_tile.form.treerepr(prefix='_'))

        # empty extraction
        data = form_tile.form.extract(request=request)
        self.assertEqual(data.fetch('tokenform.value').extracted, UNSET)
        self.assertEqual(data.fetch('tokenform.valid_from').extracted, None)
        self.assertEqual(data.fetch('tokenform.valid_to').extracted, None)
        self.assertEqual(data.fetch('tokenform.usage_count').extracted, UNSET)
        self.assertEqual(data.fetch('tokenform.lock_time').extracted, UNSET)

        # extraction with empty values
        request.params['tokenform.value'] = ''
        request.params['tokenform.valid_from'] = ''
        request.params['tokenform.valid_from.time'] = ''
        request.params['tokenform.valid_to'] = ''
        request.params['tokenform.valid_to.time'] = ''
        request.params['tokenform.usage_count'] = ''
        request.params['tokenform.lock_time'] = ''
        request.params['action.tokenform.save'] = ''

        data = form_tile.form.extract(request=request)
        self.assertEqual(data.fetch('tokenform.value').extracted, '')
        self.assertEqual(data.fetch('tokenform.valid_from').extracted, None)
        self.assertEqual(data.fetch('tokenform.valid_to').extracted, None)
        self.assertEqual(data.fetch('tokenform.usage_count').extracted, -1.)
        self.assertEqual(data.fetch('tokenform.lock_time').extracted, 0)

        # extraction with values
        request.params['tokenform.value'] = 'token value'
        request.params['tokenform.valid_from'] = '21.9.2023'
        request.params['tokenform.valid_from.time'] = '10:00'
        request.params['tokenform.valid_to'] = '21.9.2023'
        request.params['tokenform.valid_to.time'] = '16:00'
        request.params['tokenform.usage_count'] = '1'
        request.params['tokenform.lock_time'] = '100'

        data = form_tile.form.extract(request=request)
        self.assertEqual(data.fetch('tokenform.value').extracted, 'token value')
        self.assertEqual(
            data.fetch('tokenform.valid_from').extracted,
            datetime(2023, 9, 21, 10, 0)
        )
        self.assertEqual(
            data.fetch('tokenform.valid_to').extracted,
            datetime(2023, 9, 21, 16, 0)
        )
        self.assertEqual(data.fetch('tokenform.usage_count').extracted, 1)
        self.assertEqual(data.fetch('tokenform.lock_time').extracted, 100)

        # value validation
        session = get_session(request)

        token = TokenRecord()
        token.uid = uuid.uuid4()
        token.value = 'value'
        session.add(token)
        session.commit()

        request.params['tokenform.value'] = 'value'
        data = form_tile.form.extract(request=request)
        self.assertEqual(
            data.fetch('tokenform.value').errors,
            [ExtractionError('value_already_used')]
        )
        request.params['tokenform.value'] = 'token value'

        # time range validation
        request.params['tokenform.valid_from'] = '21.9.2023'
        request.params['tokenform.valid_from.time'] = '10:00'
        request.params['tokenform.valid_to'] = ''
        request.params['tokenform.valid_to.time'] = ''

        data = form_tile.form.extract(request=request)
        self.assertEqual(
            data.fetch('tokenform.valid_from').extracted,
            datetime(2023, 9, 21, 10, 0)
        )
        self.assertEqual(data.fetch('tokenform.valid_to').extracted, None)

        request.params['tokenform.valid_from'] = ''
        request.params['tokenform.valid_from.time'] = ''
        request.params['tokenform.valid_to'] = '21.9.2023'
        request.params['tokenform.valid_to.time'] = '16:00'

        data = form_tile.form.extract(request=request)
        self.assertEqual(data.fetch('tokenform.valid_from').extracted, None)
        self.assertEqual(
            data.fetch('tokenform.valid_to').extracted,
            datetime(2023, 9, 21, 16, 0)
        )

        request.params['tokenform.valid_from'] = '22.9.2023'
        request.params['tokenform.valid_from.time'] = '00:00'
        request.params['tokenform.valid_to'] = '21.9.2023'
        request.params['tokenform.valid_to.time'] = '00:00'

        data = form_tile.form.extract(request=request)
        self.assertEqual(data.fetch('tokenform.valid_from').errors, [])
        self.assertEqual(
            data.fetch('tokenform.valid_to').errors,
            [ExtractionError('timerange_error')]
        )

    @principals(users={'admin': {}}, roles={'admin': ['manager']})
    @sql_testing.delete_table_records(TokenRecord)
    def test_TokenAddForm(self):
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

        # prepare request, token gets created with default values
        request.params['tokenform.value'] = ''
        request.params['tokenform.valid_from'] = ''
        request.params['tokenform.valid_from.time'] = ''
        request.params['tokenform.valid_to'] = ''
        request.params['tokenform.valid_to.time'] = ''
        request.params['tokenform.usage_count'] = ''
        request.params['tokenform.lock_time'] = ''
        request.params['action.tokenform.save'] = '1'

        # save token
        with self.layer.authenticated('admin'):
            form_tile(token, request)

        # check if token has been added
        self.assertEqual(len(tokens), 1)
        token = tokens[token.name]
        self.assertEqual(token.attrs['value'], token.name)
        self.assertEqual(token.attrs['valid_from'], None)
        self.assertEqual(token.attrs['valid_to'], None)
        self.assertEqual(token.attrs['usage_count'], -1)
        self.assertEqual(token.attrs['lock_time'], 0)

        # create another token with custom values
        tokens.clear()
        tokens()
        token = TokenNode(parent=tokens)

        request.params['tokenform.value'] = 'token value'
        request.params['tokenform.valid_from'] = '21.9.2023'
        request.params['tokenform.valid_from.time'] = '10:00'
        request.params['tokenform.valid_to'] = '22.9.2023'
        request.params['tokenform.valid_to.time'] = '12:00'
        request.params['tokenform.usage_count'] = '10'
        request.params['tokenform.lock_time'] = '100'
        request.params['action.tokenform.save'] = '1'

        # save token
        with self.layer.authenticated('admin'):
            form_tile(token, request)

        self.assertEqual(len(tokens), 1)
        token = tokens[token.name]
        self.assertEqual(token.attrs['value'], 'token value')
        self.assertEqual(token.attrs['valid_from'], datetime(2023, 9, 21, 10, 0))
        self.assertEqual(token.attrs['valid_to'], datetime(2023, 9, 22, 12, 0))
        self.assertEqual(token.attrs['usage_count'], 10)
        self.assertEqual(token.attrs['lock_time'], 100)

    @principals(users={'admin': {}}, roles={'admin': ['manager']})
    @sql_testing.delete_table_records(TokenRecord)
    def test_TokenEditForm(self):
        request = self.layer.new_request()

        # create token
        tokens = get_root()['tokens']
        token_uid = str(uuid.uuid4())
        token = tokens[token_uid] = TokenNode()
        token.attrs['value'] = 'token value'
        token.attrs['valid_from'] = datetime(2023, 9, 21, 10, 0)
        token.attrs['valid_to'] = datetime(2023, 9, 22, 12, 0)
        token.attrs['usage_count'] = 10
        token.attrs['lock_time'] = 100

        # prepare token form
        form_tile = TokenEditForm(attribute='render')
        form_tile.model = token
        form_tile.request = request
        form_tile.action_resource = 'tokenform'
        form_tile.prepare()

        # prepare request
        request.params['tokenform.value'] = ''
        request.params['tokenform.valid_from'] = '21.9.2023'
        request.params['tokenform.valid_from.time'] = '08:00'
        request.params['tokenform.valid_to'] = '21.9.2023'
        request.params['tokenform.valid_to.time'] = '18:00'
        request.params['tokenform.usage_count'] = '-1'
        request.params['tokenform.lock_time'] = '0'
        request.params['action.tokenform.save'] = '1'

        # save token
        with self.layer.authenticated('admin'):
            form_tile(token, request)

        # check token has been edited
        self.assertEqual(token.attrs['value'], token.name)
        self.assertEqual(token.attrs['valid_from'], datetime(2023, 9, 21, 8, 0))
        self.assertEqual(token.attrs['valid_to'], datetime(2023, 9, 21, 18, 0))
        self.assertEqual(token.attrs['usage_count'], -1)
        self.assertEqual(token.attrs['lock_time'], 0)


class TestTokenViews(NodeTestCase):
    layer = tokens_layer

    def test_qr_code(self):
        data = qr_code('A')
        self.assertTrue(data.startswith(b'\x89PNG'))

    def test_b64_qr_code(self):
        data = b64_qr_code('A')
        self.assertTrue(data.startswith('data:image/png;base64'))

    @principals(users={'admin': {}}, roles={'admin': ['manager']})
    def test_download_qr_code(self):
        tokens = get_root()['tokens']
        token_uid = uuid.UUID('57b9f6b1-b4c8-4aeb-9f12-22ab482546a2')
        token = tokens[str(token_uid)] = TokenNode()
        token.attrs['value'] = 'value'

        request = self.layer.new_request()
        with self.layer.authenticated('admin'):
            res = render_view_to_response(token, request, 'qr_code')
        self.assertTrue(res.body.startswith(b'\x89PNG'))
        self.assertEqual(res.content_type, 'image/png')
        self.assertEqual(
            res.content_disposition,
            'attachment;filename=57b9f6b1-b4c8-4aeb-9f12-22ab482546a2.png'
        )

    @principals(users={'admin': {}}, roles={'admin': ['manager']})
    def test_TokenContent(self):
        request = self.layer.new_request()
        token_tile = TokenContent()
        token_tile.model = TokenNode()
        token_tile.request = request
        # XXX


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


def run_tests(): # pragma: no cover
    from cone.tokens import tests
    from zope.testrunner.runner import Runner

    suite = unittest.TestSuite()
    suite.addTest(unittest.findTestCases(tests))

    runner = Runner(found_suites=[suite])
    runner.run()
    sys.exit(int(runner.failed))


if __name__ == '__main__': # pragma: no cover
    run_tests()
