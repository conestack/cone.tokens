from cone.sql.testing import SQLLayer
from cone.tokens.settings import tokens_config
import os
import shutil
import tempfile


def temp_config_file(fn):
    """Decorator for tests writing the token settings config file.

    Points ``tokens_config.config_file`` to a file in a temporary directory
    and restores the original path afterwards.
    """

    def wrapper(*a, **kw):
        config_file = tokens_config.config_file
        tempdir = tempfile.mkdtemp()
        tokens_config.config_file = os.path.join(tempdir, 'tokens.json')
        try:
            fn(*a, **kw)
        finally:
            tokens_config.config_file = config_file
            shutil.rmtree(tempdir)

    return wrapper


class TokensLayer(SQLLayer):
    def make_app(self):
        plugins = ['cone.ugm', 'cone.sql', 'cone.tokens']
        kw = dict()
        kw['cone.plugins'] = '\n'.join(plugins)
        kw['cone.tokens.config_file'] = '/tmp/tokens.json'
        super().make_app(**kw)


tokens_layer = TokensLayer()
