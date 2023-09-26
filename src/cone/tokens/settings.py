from cone.app.model import BaseNode
from cone.app.model import Metadata
from cone.app.model import Properties
from node.utils import instance_property
from pyramid.i18n import TranslationStringFactory
import json
import logging
import os

_ = TranslationStringFactory('cone.tokens')


token_cfg = Properties()
token_cfg.token_settings = ''
default_token_settings = {
    'morning': {'start': '08:00', 'end': '12:00'},
    'afternoon': {'start': '12:00', 'end': '18:00'},
    'today': {'start': '08:00', 'end': '18:00'},
    'default_locktime': '3600',
    'default_uses': '10',
}

class TokenSettings(BaseNode):

    @property
    def config_file(self):
        from cone.tokens import config_file_path
        return config_file_path

    @property
    def attrs(self):
        config_file = self.config_file
        if not os.path.isfile(config_file):
            msg = 'Configuration file {} not exists. Created new file.'.format(config_file)
            logging.info(msg)
            with open(config_file, "w") as f:
                json.dump(default_token_settings, f)
            return default_token_settings
        with open(config_file) as f:
            data = json.load(f)
        return data

    @instance_property
    def metadata(self):
        metadata = Metadata()
        metadata.title = _(
            'token_settings_node',
            default='Token Settings')
        metadata.description = _(
            'token_settings_node_description',
            default='Token definition settings'
        )
        return metadata
