from cone.app import get_root
from cone.sql import get_session
from cone.sql import testing as sql_testing
from cone.tokens.browser.token import TokenAddForm
from cone.tokens.browser.token import TokenContent
from cone.tokens.browser.token import TokenEditForm
from cone.tokens.browser.token import TokenForm
from cone.tokens.browser.token import b64_qr_code
from cone.tokens.browser.token import qr_code
from cone.tokens.model import TokenNode
from cone.tokens.model import TokenRecord
from cone.tokens.settings import tokens_config
from cone.tokens.tests import tokens_layer
from cone.ugm import testing
from cone.ugm.testing import principals
from datetime import datetime 
from node.tests import NodeTestCase
from node.utils import UNSET
from pyramid.view import render_view_to_response
from yafowil.base import ExtractionError
import os
import uuid


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
        token = TokenNode()
        tokens[str(token.uuid)] = token
        token.attrs['value'] = 'value'

        request = self.layer.new_request()
        with self.layer.authenticated('admin'):
            res = render_view_to_response(token, request, 'qr_code')
        self.assertTrue(res.body.startswith(b'\x89PNG'))
        self.assertEqual(res.content_type, 'image/png')
        self.assertEqual(
            res.content_disposition,
            f'attachment;filename={token.name}.png'
        )

    @principals(users={'admin': {}}, roles={'admin': ['manager']})
    def test_TokenContent(self):
        request = self.layer.new_request()
        token_tile = TokenContent()
        token_tile.model = TokenNode()
        token_tile.request = request
        # XXX


class TestTokenForms(NodeTestCase):
    layer = tokens_layer

    @testing.temp_directory
    def test_TokenForm(self, tempdir):
        tokens_config.config_file = os.path.join(tempdir, 'tokens.json')
        request = self.layer.new_request()

        # create token
        tokens = get_root()['tokens']
        token = TokenNode(parent=tokens)

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
        self.assertEqual(data.fetch('tokenform.usage_count').extracted, 0)
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
    @testing.temp_directory
    def test_TokenAddForm(self, tempdir):
        tokens_config.config_file = os.path.join(tempdir, 'tokens.json')
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
        self.assertEqual(token.attrs['usage_count'], 0)
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
    @testing.temp_directory
    def test_TokenEditForm(self, tempdir):
        tokens_config.config_file = os.path.join(tempdir, 'tokens.json')
        request = self.layer.new_request()

        # create token
        tokens = get_root()['tokens']
        token = TokenNode()
        tokens[str(token.uuid)] = token
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
