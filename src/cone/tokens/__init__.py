from cone.app import main_hook
from cone.tokens.browser import configure_resources
from cone.tokens.model import TokenContainer
import cone.app
import logging


logger = logging.getLogger('cone.tokens')


@main_hook
def initialize_tokens(config, global_config, settings):
    # application startup initialization

    # static resources
    configure_resources(config, settings)

    # add translation
    config.add_translation_dirs('cone.tokens:locale/')

    # scan browser package
    config.scan('cone.tokens.browser')

    # register entry node
    cone.app.register_entry('tokens', TokenContainer)
