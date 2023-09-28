from bda.intellidatetime import DateTimeConversionError
from bda.intellidatetime import convert
from cone.app.browser import render_main_template
from cone.app.browser.actions import LinkAction
from cone.app.browser.contextmenu import context_menu_item
from cone.app.browser.layout import ProtectedContentTile
from cone.app.browser.utils import make_url
from cone.app.browser.utils import request_property
from cone.sql import get_session
from cone.tile import tile
from cone.tokens.browser.token import b64_qr_code
from cone.tokens.model import TokenContainer
from cone.tokens.model import TokenRecord
from cone.tokens.settings import get_settings_node
from pyramid.i18n import TranslationStringFactory
from pyramid.view import view_config
import json


_ = TranslationStringFactory('cone.tokens')


@tile(
    name='content',
    path='templates/tokens.pt',
    interface=TokenContainer,
    permission='view')
class TokensContent(ProtectedContentTile):
    ...


@context_menu_item(group='contentviews', name='tokens_overview')
class TokensOverviewAction(LinkAction):
    text = _('tokens_overview', default='Overview')
    icon = 'glyphicon glyphicon-list-alt'
    action = 'tokens_overview:#content:inner'
    path = 'href'

    @property
    def href(self):
        return make_url(self.request, node=self.model, resource='tokens_overview')

    @property
    def display(self):
        return isinstance(self.model, TokenContainer)

    @property
    def selected(self):
        return self.action_scope == 'tokens_overview'


@view_config(name='tokens_overview', context=TokenContainer, permission='view')
def tokens_overview(model, request):
    return render_main_template(model, request, 'tokens_overview')


@tile(
    name='tokens_overview',
    path='templates/tokens_overview.pt',
    interface=TokenContainer,
    permission='view')
class TokensOverview(ProtectedContentTile):

    @request_property
    def token_settings(self):
        return json.dumps({
            'base_url': self.nodeurl
        })

    @request_property
    def start(self):
        try:
            return convert(self.request.params.get('start', ''), locale='de')
        except DateTimeConversionError:
            return None

    @request_property
    def end(self):
        try:
            return convert(self.request.params.get('end', ''), locale='de')
        except DateTimeConversionError:
            return None

    @property
    def tokens(self):
        action = self.request.params.get('ajax.action', None)
        if not action:
            return
        start = self.start
        end = self.end
        session = get_session(self.request)
        query = session.query(TokenRecord)
        if start:
            query = query.filter(TokenRecord.created >= start)
        if end:
            query = query.filter(TokenRecord.created <= end)
        tokens = query.all()
        return tokens

    def qrcode(self, value):
        return b64_qr_code(value)

    def format_date(self, date, default=''):
        if not date:
            return default
        return date.strftime('%d.%m.%Y')
