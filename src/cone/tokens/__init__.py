from cone.app import main_hook
import logging

logger = logging.getLogger('cone.tokens')

@main_hook
def initialize_tokens(config, global_config, settings):
    # application startup initialization

    # static resources
    #configure_resources(config, settings)

    # scan browser package
    #config.scan('cone.tokens.browser')
    pass