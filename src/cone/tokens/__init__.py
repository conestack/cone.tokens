from cone.app import main_hook
from cone.tokens.model import Tokens
import logging
import cone.app

logger = logging.getLogger('cone.tokens')

@main_hook
def initialize_tokens(config, global_config, settings):
    # application startup initialization

    # static resources
    #configure_resources(config, settings)

    # scan browser package
    #config.scan('cone.tokens.browser')
    cone.app.register_entry('tokens', Tokens)
    pass