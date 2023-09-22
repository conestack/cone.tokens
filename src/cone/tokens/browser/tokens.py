from cone.app.browser.actions import LinkAction
from cone.app.browser.contextmenu import context_menu_item
from cone.app.browser.layout import ProtectedContentTile
from cone.tile import tile
from cone.tokens.model import TokenContainer
from cone.app.browser.utils import make_url
from pyramid.i18n import get_localizer
from pyramid.i18n import TranslationStringFactory
from cone.sql import get_session
from cone.tokens.model import TokenRecord
from pyramid.view import view_config
from cone.app.browser.utils import request_property
from cone.tokens.browser.token import b64_qr_code

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

@tile(
    name='tokens_overview',
    path='templates/tokens_overview.pt',
    interface=TokenContainer,
    permission='view')
class TokensOverview(ProtectedContentTile):

    @property
    def tokens(self):
        session = get_session(self.request)
        tokens = session.query(TokenRecord).all()
        return tokens

    def qrcode(self, value):
        return b64_qr_code(value)