from cone.app import main_hook
from cone.app import register_config
from cone.tokens.browser import configure_resources
from cone.tokens.model import TokenContainer
from cone.tokens.settings import time_cfg
from cone.tokens.settings import TimeSettings
import cone.app
import logging


logger = logging.getLogger('cone.tokens')


@main_hook
def initialize_tokens(config, global_config, settings):
    # application startup initialization

    # config file locations
    time_cfg.time_settings = settings.get('time.config', '')

    # settings
    register_config('time', TimeSettings)

    # static resources
    configure_resources(config, settings)

    # add translation
    config.add_translation_dirs('cone.tokens:locale/')

    # scan browser package
    config.scan('cone.tokens.browser')

    # register entry node
    cone.app.register_entry('tokens', TokenContainer)
