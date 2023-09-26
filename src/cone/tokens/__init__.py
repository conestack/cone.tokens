from cone.app import import_from_string
from cone.app import main_hook
from cone.app import register_config
from cone.tokens.browser import configure_resources
from cone.tokens.model import TokenContainer
from cone.tokens.settings import token_cfg
from cone.tokens.settings import TokenSettings
import cone.app
import logging


logger = logging.getLogger('cone.tokens')
config_file_path = None

@main_hook
def initialize_tokens(config, global_config, settings):
    # application startup initialization

    global config_file_path
    config_file_path = settings['cone.tokens.config_file']

    # settings
    register_config('token_settings', TokenSettings)

    # static resources
    configure_resources(config, settings)

    # add translation
    config.add_translation_dirs('cone.tokens:locale/')

    # scan browser package
    config.scan('cone.tokens.browser')

    # register entry node
    tokens_entry_factory = settings.get(
        'cone.tokens.entryfactory',
        'cone.tokens.model.TokenContainer'
    )
    cone.app.register_entry('tokens', import_from_string(tokens_entry_factory))
