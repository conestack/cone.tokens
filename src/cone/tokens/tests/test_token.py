from cone.app import get_root
from cone.app.browser.actions import ActionContext
from cone.sql import get_session
from cone.sql import testing as sql_testing
from cone.tokens.browser.token import b64_qr_code
from cone.tokens.browser.token import qr_code
from cone.tokens.browser.token import TokenAddForm
from cone.tokens.browser.token import TokenContent
from cone.tokens.browser.token import TokenEditForm
from cone.tokens.browser.token import TokenForm
from cone.tokens.browser.tokens import TokensOverview
from cone.tokens.browser.tokens import TokensOverviewAction
from cone.tokens.model import TokenNode
from cone.tokens.model import TokenRecord
from cone.tokens.settings import default_token_settings
from cone.tokens.tests import temp_config_file
from cone.tokens.tests import tokens_layer
from cone.ugm.testing import principals
from datetime import datetime
from datetime import timedelta
from node.tests import NodeTestCase
from node.utils import UNSET
from pyramid.view import render_view_to_response
from yafowil.base import ExtractionError
import json
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
    @sql_testing.delete_table_records(TokenRecord)
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
        self.assertEqual(res.content_disposition, f'attachment;filename={token.name}.png')

    @temp_config_file
    def test_TokenContent_token_settings(self):
        tokens = get_root()['tokens']
        token = TokenNode(name='token', parent=tokens)
        token_tile = TokenContent()
        token_tile.model = token
        token_tile.request = self.layer.new_request()
        self.assertEqual(
            json.loads(token_tile.token_settings),
            {
                'base_url': 'http://example.com/tokens/token',
                'timeranges': default_token_settings,
            },
        )

    def test_TokenContent_displays_token_value_as_qr_code(self):
        token_tile = self._token_content_tile(value='value')
        self.assertEqual(token_tile.qrcode, b64_qr_code('value'))

    def test_TokenContent_lock_time_seconds(self):
        token_tile = self._token_content_tile(lock_time=100)
        self.assertEqual(token_tile.lock_time_seconds, '100 sec')

    def test_TokenContent_token_without_restrictions_is_active(self):
        token_tile = self._token_content_tile(usage_count=-1)
        self.assertTrue(token_tile.is_active)
        self.assertEqual(token_tile.active_label, 'Active')
        self.assertEqual(token_tile.cssclass, 'list-group-item-success')

    def test_TokenContent_token_within_time_range_is_active(self):
        now = datetime.now()
        token_tile = self._token_content_tile(
            usage_count=1,
            valid_from=now - timedelta(days=1),
            valid_to=now + timedelta(days=1),
        )
        self.assertTrue(token_tile.is_active)

    def test_TokenContent_used_up_token_is_inactive(self):
        token_tile = self._token_content_tile(usage_count=0)
        self.assertFalse(token_tile.is_active)
        self.assertEqual(token_tile.active_label, 'Inactive')
        self.assertEqual(token_tile.cssclass, 'list-group-item-danger')

    def test_TokenContent_expired_token_is_inactive(self):
        token_tile = self._token_content_tile(
            usage_count=-1, valid_to=datetime.now() - timedelta(days=1)
        )
        self.assertFalse(token_tile.is_active)

    def test_TokenContent_not_yet_valid_token_is_inactive(self):
        token_tile = self._token_content_tile(
            usage_count=-1, valid_from=datetime.now() + timedelta(days=1)
        )
        self.assertFalse(token_tile.is_active)

    def test_TokenContent_format_date(self):
        token_tile = self._token_content_tile()
        self.assertEqual(
            token_tile.format_date(datetime(2023, 9, 21, 10, 30, 15)),
            '21.09.2023, 10:30:15',
        )
        self.assertEqual(token_tile.format_date(None), 'Unlimited')

    def _token_content_tile(self, **attrs):
        token = TokenNode()
        token.attrs.update(attrs)
        token_tile = TokenContent()
        token_tile.model = token
        token_tile.request = self.layer.new_request()
        return token_tile


class TestTokenForms(NodeTestCase):
    layer = tokens_layer

    @sql_testing.delete_table_records(TokenRecord)
    @temp_config_file
    def test_TokenForm(self):
        request = self.layer.new_request()

        # create token
        tokens = get_root()['tokens']
        token = TokenNode(parent=tokens)

        class TestTokenForm(TokenForm):
            def next(self, request): ...

        # prepare token form
        form_tile = TestTokenForm(attribute='render')
        form_tile.model = token
        form_tile.request = request
        form_tile.action_resource = 'tokenform'
        form_tile.prepare()

        # token form structure
        self.assertEqual(form_tile.form.name, 'tokenform')
        self.checkOutput(
            """
        <class 'yafowil.base.Widget'>: tokenform
        __<class 'yafowil.base.Widget'>: value
        __<class 'yafowil.base.Widget'>: valid_from
        __<class 'yafowil.base.Widget'>: valid_to
        __<class 'yafowil.base.Widget'>: usage_count
        __<class 'yafowil.base.Widget'>: lock_time
        __<class 'yafowil.base.Widget'>: save
        __<class 'yafowil.base.Widget'>: cancel
        """,
            form_tile.form.treerepr(prefix='_'),
        )

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
            data.fetch('tokenform.valid_from').extracted, datetime(2023, 9, 21, 10, 0)
        )
        self.assertEqual(
            data.fetch('tokenform.valid_to').extracted, datetime(2023, 9, 21, 16, 0)
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
            data.fetch('tokenform.value').errors, [ExtractionError('value_already_used')]
        )
        request.params['tokenform.value'] = 'token value'

        # time range validation
        request.params['tokenform.valid_from'] = '21.9.2023'
        request.params['tokenform.valid_from.time'] = '10:00'
        request.params['tokenform.valid_to'] = ''
        request.params['tokenform.valid_to.time'] = ''

        data = form_tile.form.extract(request=request)
        self.assertEqual(
            data.fetch('tokenform.valid_from').extracted, datetime(2023, 9, 21, 10, 0)
        )
        self.assertEqual(data.fetch('tokenform.valid_to').extracted, None)

        request.params['tokenform.valid_from'] = ''
        request.params['tokenform.valid_from.time'] = ''
        request.params['tokenform.valid_to'] = '21.9.2023'
        request.params['tokenform.valid_to.time'] = '16:00'

        data = form_tile.form.extract(request=request)
        self.assertEqual(data.fetch('tokenform.valid_from').extracted, None)
        self.assertEqual(
            data.fetch('tokenform.valid_to').extracted, datetime(2023, 9, 21, 16, 0)
        )

        request.params['tokenform.valid_from'] = '22.9.2023'
        request.params['tokenform.valid_from.time'] = '00:00'
        request.params['tokenform.valid_to'] = '21.9.2023'
        request.params['tokenform.valid_to.time'] = '00:00'

        data = form_tile.form.extract(request=request)
        self.assertEqual(data.fetch('tokenform.valid_from').errors, [])
        self.assertEqual(
            data.fetch('tokenform.valid_to').errors, [ExtractionError('timerange_error')]
        )

        # valid to must be after valid from, same time is invalid too
        request.params['tokenform.valid_to'] = '22.9.2023'

        data = form_tile.form.extract(request=request)
        self.assertEqual(
            data.fetch('tokenform.valid_to').errors, [ExtractionError('timerange_error')]
        )

    @principals(users={'admin': {}}, roles={'admin': ['manager']})
    @sql_testing.delete_table_records(TokenRecord)
    @temp_config_file
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
    @temp_config_file
    def test_TokenEditForm(self):
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


class TestTokensOverview(NodeTestCase):
    layer = tokens_layer

    def test_TokensOverviewAction(self):
        tokens = get_root()['tokens']
        request = self.layer.new_request()
        action = TokensOverviewAction()
        action.model = tokens
        action.request = request
        self.assertEqual(action.href, 'http://example.com/tokens/tokens_overview')
        self.assertTrue(action.display)
        self.assertFalse(action.selected)

        ActionContext(tokens, request, 'tokens_overview')
        self.assertTrue(action.selected)

        action.model = TokenNode(parent=tokens)
        self.assertFalse(action.display)

    @principals(users={'admin': {}}, roles={'admin': ['manager']})
    @sql_testing.delete_table_records(TokenRecord)
    def test_tokens_overview(self):
        tokens = get_root()['tokens']
        request = self.layer.new_request()
        with self.layer.authenticated('admin'):
            res = render_view_to_response(tokens, request, 'tokens_overview')
        self.assertTrue(res.text.find('tokens-overview-container') > -1)

    def test_TokensOverview_token_settings(self):
        overview_tile = self._tokens_overview_tile()
        self.assertEqual(
            json.loads(overview_tile.token_settings),
            {'base_url': 'http://example.com/tokens'},
        )

    def test_TokensOverview_parses_start_and_end_dates(self):
        overview_tile = self._tokens_overview_tile(start='21.9.2023', end='22.9.2023')
        self.assertEqual(overview_tile.start, datetime(2023, 9, 21))
        self.assertEqual(overview_tile.end, datetime(2023, 9, 22))

    def test_TokensOverview_ignores_invalid_start_and_end_dates(self):
        overview_tile = self._tokens_overview_tile(start='foo', end='bar')
        self.assertIsNone(overview_tile.start)
        self.assertIsNone(overview_tile.end)

    def test_TokensOverview_no_tokens_without_ajax_action(self):
        overview_tile = self._tokens_overview_tile()
        self.assertIsNone(overview_tile.tokens)

    @sql_testing.delete_table_records(TokenRecord)
    def test_TokensOverview_tokens(self):
        request = self.layer.new_request()
        session = get_session(request)
        for value, created in [
            ('first', datetime(2023, 9, 20)),
            ('second', datetime(2023, 9, 21)),
            ('third', datetime(2023, 9, 22)),
        ]:
            token = TokenRecord()
            token.uid = uuid.uuid4()
            token.value = value
            token.created = created
            session.add(token)
        session.commit()

        def token_values(**params):
            overview_tile = self._tokens_overview_tile(
                **{'ajax.action': 'tokens_overview'}, **params
            )
            return sorted(token.value for token in overview_tile.tokens)

        self.assertEqual(token_values(), ['first', 'second', 'third'])
        self.assertEqual(token_values(start='21.9.2023'), ['second', 'third'])
        self.assertEqual(token_values(end='21.9.2023'), ['first', 'second'])
        self.assertEqual(token_values(start='21.9.2023', end='21.9.2023'), ['second'])

    def test_TokensOverview_qrcode(self):
        overview_tile = self._tokens_overview_tile()
        self.assertEqual(overview_tile.qrcode('value'), b64_qr_code('value'))

    def test_TokensOverview_format_date(self):
        overview_tile = self._tokens_overview_tile()
        self.assertEqual(overview_tile.format_date(datetime(2023, 9, 21)), '21.09.2023')
        self.assertEqual(overview_tile.format_date(None), '')
        self.assertEqual(overview_tile.format_date(None, default='-'), '-')

    def _tokens_overview_tile(self, **params):
        request = self.layer.new_request()
        request.params.update(params)
        overview_tile = TokensOverview()
        overview_tile.model = get_root()['tokens']
        overview_tile.request = request
        return overview_tile
