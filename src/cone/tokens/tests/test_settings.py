from cone.app import get_root
from cone.tokens.browser.settings import TokenSettingsForm
from cone.tokens.settings import token_cfg
from cone.tokens.settings import TokenSettings
from cone.tokens.tests import tokens_layer
from cone.ugm import testing
from node.tests import NodeTestCase
from node.utils import UNSET
import json
import os


class TestSettings(NodeTestCase):
    layer = tokens_layer

    @testing.temp_directory
    def test_model_settings(self, tempdir):
        path = os.path.join(tempdir, 'tokens.json')

        class MyTokenSettings(TokenSettings):
            config_file = path

        # default - no config file exists
        settings = MyTokenSettings()
        attrs = settings.attrs
        self.assertEqual(attrs['morning']['start'], '08:00')
        self.assertEqual(attrs['morning']['end'], '12:00')
        self.assertEqual(attrs['afternoon']['start'], '12:00')
        self.assertEqual(attrs['afternoon']['end'], '18:00')
        self.assertEqual(attrs['today']['start'], '08:00')
        self.assertEqual(attrs['today']['end'], '18:00')
        self.assertEqual(attrs['default_locktime'], '3600')
        self.assertEqual(attrs['default_uses'], '10')

        # config file exists
        with open(path, 'w') as f:
            attrs['morning']['start'] = '09:00'
            attrs['default_locktime'] = '2000'
            json.dump(attrs, f)

        attrs = settings.attrs
        self.assertEqual(attrs['morning']['start'], '09:00')
        self.assertEqual(attrs['default_locktime'], '2000')

    @testing.temp_directory
    def test_BrowserSettingsForm(self, tempdir):
        config_file = os.path.join(tempdir, 'tokens.json')
        token_cfg.token_settings = config_file
        TokenSettings.config_file = config_file

        model = get_root()['settings']['token_settings']
        request = self.layer.new_request()

        TokenSettingsForm.config_file = config_file
        tile = TokenSettingsForm()
        tile.model = model
        tile.request = request
        tile.prepare()

        form = tile.form
        self.assertEqual(form.keys(), [
            'morning',
            'afternoon',
            'today',
            'default_locktime',
            'default_uses',
            'save',
            'cancel',
            'came_from'
        ])
        self.assertEqual(form['morning'].keys(), ['start', 'end'])
        self.assertEqual(form['afternoon'].keys(), ['start', 'end'])
        self.assertEqual(form['today'].keys(), ['start', 'end'])

        # extract
        data = form.extract(request=request)
        morning = data.fetch('tokensettingsform.morning')
        self.assertEqual(morning.extracted['start'], UNSET)
        self.assertEqual(morning.extracted['end'], UNSET)
        afternoon = data.fetch('tokensettingsform.afternoon')
        self.assertEqual(afternoon.extracted['start'], UNSET)
        self.assertEqual(afternoon.extracted['end'], UNSET)
        today = data.fetch('tokensettingsform.today')
        self.assertEqual(today.extracted['start'], UNSET)
        self.assertEqual(today.extracted['end'], UNSET)
        self.assertEqual(
            data.fetch('tokensettingsform.default_locktime').extracted,
            UNSET
        )
        self.assertEqual(
            data.fetch('tokensettingsform.default_uses').extracted,
            UNSET
        )

        # save
        request.params['tokensettingsform.morning.start'] = '9:00'
        request.params['tokensettingsform.morning.end'] = '10:00'
        request.params['tokensettingsform.afternoon.start'] = '13:00'
        request.params['tokensettingsform.afternoon.end'] = '19:00'
        request.params['tokensettingsform.today.start'] = '9:00'
        request.params['tokensettingsform.today.end'] = '19:00'
        request.params['tokensettingsform.default_locktime'] = '2000'
        request.params['tokensettingsform.default_uses'] = '5'
        data = tile.form.extract(request=request)
        tile.save(model, data)

        with open(config_file) as f:
            form_data = json.load(f)
        self.assertEqual(form_data['morning']['start'], '09:00')
        self.assertEqual(form_data['morning']['end'], '10:00')
        self.assertEqual(form_data['afternoon']['start'], '13:00')
        self.assertEqual(form_data['afternoon']['end'], '19:00')
        self.assertEqual(form_data['today']['start'], '09:00')
        self.assertEqual(form_data['today']['end'], '19:00')
        self.assertEqual(form_data['default_locktime'], 2000)
        self.assertEqual(form_data['default_uses'], 5)