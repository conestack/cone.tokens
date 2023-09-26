from cone.app.model import BaseNode
from cone.app.model import Metadata
from cone.app.model import Properties
from node.utils import instance_property
from pyramid.i18n import TranslationStringFactory
import json
import os

_ = TranslationStringFactory('cone.tokens')


token_cfg = Properties()
token_cfg.token_settings = ''

class TokenSettings(BaseNode):

    @property
    def config_file(self):
        from cone.tokens import config_file_path
        return config_file_path

    @property
    def attrs(self):
        config_file = self.config_file
        if not os.path.isfile(config_file):
            msg = 'Configuration file {} not exists.'.format(config_file)
            raise ValueError(msg)
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
