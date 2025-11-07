from cone.sql.testing import SQLLayer


class TokensLayer(SQLLayer):

    def make_app(self):
        plugins = [
            'cone.ugm',
            'cone.sql',
            'cone.tokens'
        ]
        kw = dict()
        kw['cone.plugins'] = '\n'.join(plugins)
        kw['cone.tokens.config_file'] = '/tmp/tokens.json'
        super().make_app(**kw)


tokens_layer = TokensLayer()
