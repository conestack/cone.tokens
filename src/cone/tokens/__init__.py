from cone.app import import_from_string
from cone.app import main_hook
from cone.app import register_config
from cone.tokens.browser import configure_resources
from cone.tokens.settings import TokenSettings
from cone.tokens.settings import tokens_config
import cone.app
import logging


logger = logging.getLogger('cone.tokens')


@main_hook
def initialize_tokens(config, global_config, settings):
    # application startup initialization

    tokens_config.config_file = settings['cone.tokens.config_file']
    tokens_config.settings_node_path = settings.get(
        'cone.tokens.settings_node_path',
        'settings/token_settings'
    ).split('/')

    # register entry node
    tokens_entry_factory = settings.get(
        'cone.tokens.entryfactory',
        'cone.tokens.model.TokenContainer'
    )
    cone.app.register_entry('tokens', import_from_string(tokens_entry_factory))

    # settings
    register_config('token_settings', TokenSettings)

    # static resources
    configure_resources(config, settings)

    # add translation
    config.add_translation_dirs('cone.tokens:locale/')

    # scan browser package
    config.scan('cone.tokens.browser')
