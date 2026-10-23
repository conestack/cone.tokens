from cone.app import get_root
from cone.tokens.browser.settings import TokenSettingsForm
from cone.tokens.settings import TokenSettings
from cone.tokens.settings import get_settings_node
from cone.tokens.settings import tokens_config
from cone.tokens.tests import temp_config_file
from cone.tile import render_tile
from cone.tokens.tests import tokens_layer
from cone.ugm import testing
from node.tests import NodeTestCase
from node.utils import UNSET
from yafowil.base import ExtractionError
import json


class TestSettings(NodeTestCase):
    layer = tokens_layer

    @temp_config_file
    def test_model_settings(self):

        # default - no config file exists
        settings = TokenSettings()
        attrs = settings.attrs
        self.assertEqual(attrs['morning']['start'], '08:00')
        self.assertEqual(attrs['morning']['end'], '12:00')
        self.assertEqual(attrs['afternoon']['start'], '12:00')
        self.assertEqual(attrs['afternoon']['end'], '18:00')
        self.assertEqual(attrs['today']['start'], '08:00')
        self.assertEqual(attrs['today']['end'], '18:00')
        self.assertEqual(attrs['default_locktime'], 0)
        self.assertEqual(attrs['default_usage_count'], 0)

        # config file exists
        with open(tokens_config.config_file, 'w') as f:
            attrs['morning']['start'] = '09:00'
            attrs['default_locktime'] = '2000'
            json.dump(attrs, f)

        attrs = settings.attrs
        self.assertEqual(attrs['morning']['start'], '09:00')
        self.assertEqual(attrs['default_locktime'], '2000')

    def test_model_settings_metadata(self):
        metadata = TokenSettings().metadata
        self.assertEqual(metadata.title, 'token_settings_node')
        self.assertEqual(
            metadata.description,
            'token_settings_node_description'
        )

    @testing.principals(users={'admin': {}}, roles={'admin': ['manager']})
    @temp_config_file
    def test_BrowserSettingsForm(self):
        model = get_settings_node(get_root())
        request = self.layer.new_request()

        tile = TokenSettingsForm()
        tile.model = model
        tile.request = request
        with self.layer.authenticated('admin'):
            tile.prepare()

        form = tile.form
        self.assertEqual(form.keys(), [
            'morning',
            'afternoon',
            'today',
            'default_locktime',
            'default_usage_count',
            'save',
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
            data.fetch('tokensettingsform.default_usage_count').extracted,
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
        request.params['tokensettingsform.default_usage_count'] = '5'
        data = tile.form.extract(request=request)
        tile.save(model, data)

        with open(tokens_config.config_file) as f:
            form_data = json.load(f)
        self.assertEqual(form_data['morning']['start'], '09:00')
        self.assertEqual(form_data['morning']['end'], '10:00')
        self.assertEqual(form_data['afternoon']['start'], '13:00')
        self.assertEqual(form_data['afternoon']['end'], '19:00')
        self.assertEqual(form_data['today']['start'], '09:00')
        self.assertEqual(form_data['today']['end'], '19:00')
        self.assertEqual(form_data['default_locktime'], 2000)
        self.assertEqual(form_data['default_usage_count'], 5)

    @testing.principals(users={'admin': {}}, roles={'admin': ['manager']})
    @temp_config_file
    def test_BrowserSettingsForm_start_after_end_is_invalid(self):
        model = get_settings_node(get_root())
        request = self.layer.new_request()

        tile = TokenSettingsForm()
        tile.model = model
        tile.request = request
        with self.layer.authenticated('admin'):
            tile.prepare()

        request.params['tokensettingsform.morning.start'] = '11:00'
        request.params['tokensettingsform.morning.end'] = '10:00'
        data = tile.form.extract(request=request)
        morning = data.fetch('tokensettingsform.morning')
        self.assertEqual(
            morning.errors,
            [ExtractionError('end_time_before_start_time')]
        )

    @testing.principals(users={'admin': {}}, roles={'admin': ['manager']})
    @temp_config_file
    def test_BrowserSettingsForm_rendered_in_card(self):
        model = get_settings_node(get_root())
        with self.layer.authenticated('admin'):
            rendered = render_tile(model, self.layer.new_request(), 'editform')
        self.checkOutput("""
        <div class="settings-form card mt-3">
          <h5 class="card-header">Token Settings</h5>
          <div class="card-body">
            <form...</form>
          </div>
        </div>
        """, rendered)
