from cone.app.browser.layout import ProtectedContentTile
from cone.tile import tile
from cone.tokens.model import TokenContainer


@tile(
    name='content',
    path='templates/tokens.pt',
    interface=TokenContainer,
    permission='view')
class TokensContent(ProtectedContentTile):
    ...
