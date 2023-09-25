from cone.app.model import BaseNode
from cone.app.model import Metadata
from cone.app.model import Properties
from node.utils import instance_property
from pyramid.i18n import TranslationStringFactory
import json
import os

_ = TranslationStringFactory('cone.tokens')


time_cfg = Properties()
time_cfg.time_settings = ''

class TimeSettings(BaseNode):

    @property
    def config_file(self):
        return 'time.json'

    @instance_property
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
            'time_settings_node',
            default='Time Settings')
        metadata.description = _(
            'time_settings_node_description',
            default='Time definition settings'
        )
        return metadata
