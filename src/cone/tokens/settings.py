from cone.app.model import BaseNode
from cone.app.model import Metadata
from node.utils import instance_property
from pyramid.i18n import TranslationStringFactory
import json
import logging
import os


_ = TranslationStringFactory('cone.tokens')


class TokensConfig:
    config_file = None
    settings_node_path = None


tokens_config = TokensConfig()


def get_settings_node(model):
    node = model.root
    for name in tokens_config.settings_node_path:
        node = node[name]
    return node


default_token_settings = {
    'morning': {'start': '08:00', 'end': '12:00'},
    'afternoon': {'start': '12:00', 'end': '18:00'},
    'today': {'start': '08:00', 'end': '18:00'},
    'default_locktime': 0,
    'default_usage_count': 0,
}


class TokenSettings(BaseNode):

    @property
    def attrs(self):
        config_file = tokens_config.config_file
        if not os.path.exists(config_file):
            msg = f'Configuration file {config_file} not exists. Create it.'
            logging.info(msg)
            with open(config_file, 'w') as f:
                json.dump(default_token_settings, f, indent=4)
            return default_token_settings
        with open(config_file) as f:
            data = json.load(f)
        return data

    @instance_property
    def metadata(self):
        metadata = Metadata()
        metadata.title = _('token_settings_node', default='Token Settings')
        metadata.description = _(
            'token_settings_node_description',
            default='Token definition settings'
        )
        return metadata
