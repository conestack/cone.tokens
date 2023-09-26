from cone.app.browser.authoring import ContentEditForm
from cone.app.browser.form import Form
from cone.app.browser.layout import ProtectedContentTile
from cone.app.browser.settings import SettingsBehavior
from cone.app.browser.utils import make_url
from cone.tile import tile
from cone.tokens.settings import TokenSettings
from cone.tokens.settings import tokens_config
from plumber import plumbing
from pyramid.i18n import TranslationStringFactory
from yafowil.base import ExtractionError
from yafowil.base import factory
from yafowil.compound import compound_extractor
from yafowil.persistence import node_attribute_writer
import datetime
import json


_ = TranslationStringFactory('cone.ugm')


@tile(
    name='content',
    path='templates/token_settings.pt',
    interface=TokenSettings,
    permission='manage')
class TokenSettingsContent(ProtectedContentTile):
    pass


@tile(name='editform', interface=TokenSettings, permission='edit')
@plumbing(SettingsBehavior, ContentEditForm)
class TokenSettingsForm(Form):
    action_resource = u'edit'
    form_name = 'tokensettingsform'
    show_contextmenu = False
    form_heading = _('token_settings', default='Token Settings')

    @property
    def message_factory(self):
        return _

    def timerange_extractor(self, widget, data):
        start = data.extracted['start']
        end = data.extracted['end']
        if start:
            s = start.split(':')
            s_h = int(s[0])
            s_m = int(s[1])
        if end:
            e = end.split(':')
            e_h = int(e[0])
            e_m = int(e[1])
        if start and end:
            now = datetime.datetime.now()
            dt_st = now.replace(hour=s_h, minute=s_m, second=0, microsecond=0)
            dt_end = now.replace(hour=e_h, minute=e_m, second=0, microsecond=0)
            if dt_st > dt_end:
                raise ExtractionError(_(
                    'end_time_before_start_time',
                    default='Start Time must be before End Time.'
                ))
        return {
            'start': start,
            'end': end
        }

    def prepare(self):
        action = make_url(
            self.request,
            node=self.model,
            resource=self.action_resource
        )
        form = self.form = factory('#form', name=self.form_name, props={
            'action': action,
            'persist_writer': node_attribute_writer
        })
        form['morning'] = factory(
            '#field:error:*morning:compound',
            props={
                'label': _('morning', default='Morning')
            },
            custom = {
                'morning': {
                    'extractors': [compound_extractor, self.timerange_extractor]
                }
            })
        start_required = _('start_time_required', default='Start Time is required.')
        end_required = _('end_time_required', default='End Time is required.')
        form['morning']['start'] = factory(
            '#field:time',
            value=self.model.attrs['morning']['start'],
            props={
                'required': start_required,
                'label': _('start', default='Start'),
                'timepicker': True,
                'time': True,
                'persist': True
            })
        form['morning']['end'] = factory(
            '#field:time',
            value=self.model.attrs['morning']['end'],
            props={
                'required': end_required,
                'label': _('end', default='End'),
                'timepicker': True,
                'time': True,
                'persist': True
            })
        form['afternoon'] = factory(
            '#field:error:*afternoon:compound',
            props={
                'label': _('afternoon', default='Afternoon')
            },
            custom = {
                'afternoon': {
                    'extractors': [compound_extractor, self.timerange_extractor]
                }
            })
        form['afternoon']['start'] = factory(
            '#field:time',
            value=self.model.attrs['afternoon']['start'],
            props={
                'required': start_required,
                'label': _('start', default='Start'),
                'timepicker': True,
                'time': True,
                'persist': True
            })
        form['afternoon']['end'] = factory(
            '#field:time',
            value=self.model.attrs['afternoon']['end'],
            props={
                'required': end_required,
                'label': _('end', default='End'),
                'timepicker': True,
                'time': True,
                'persist': True
            })
        form['today'] = factory(
            '#field:error:*today:compound',
            props={
                'label': _('today', default='Today')
            },
            custom = {
                'today': {
                    'extractors': [compound_extractor, self.timerange_extractor]
                }
            })
        form['today']['start'] = factory(
            '#field:time',
            value=self.model.attrs['today']['start'],
            props={
                'required': start_required,
                'label': _('start', default='Start'),
                'timepicker': True,
                'time': True,
                'persist': True
            })
        form['today']['end'] = factory(
            '#field:time',
            value=self.model.attrs['today']['end'],
            props={
                'required': end_required,
                'label': _('end', default='End'),
                'timepicker': True,
                'time': True,
                'persist': True
            })
        form['default_locktime'] = factory(
            '#field:number',
            value=self.model.attrs['default_locktime'],
            props={
                'datatype': int,
                'min': 0,
                'required': _('default_locktime_required', default='Default Locktime is required.'),
                'label': _('default_locktime', default='Default Locktime')
            })
        form['default_usage_count'] = factory(
            '#field:number',
            value=self.model.attrs['default_usage_count'],
            props={
                'datatype': int,
                'min': -1,
                'required': _('default_usage_count_required', default='Default number of uses required.'),
                'label': _('default_usage_count', default='Default Uses')
            })
        form['save'] = factory(
            'submit',
            props={
                'action': 'save',
                'expression': True,
                'handler': self.save,
                'next': self.next,
                'label': 'Save'
        })
        form['cancel'] = factory(
            'submit',
            props={
                'action': 'cancel',
                'expression': True,
                'skip': True,
                'next': self.next,
                'label': 'Cancel'
        })

    def save(self, widget, data):
        def fetch(name):
            return data.fetch(f'tokensettingsform.{name}').extracted
        with open(tokens_config.config_file, 'w') as f:
            json.dump({
                'morning': fetch('morning'),
                'afternoon': fetch('afternoon'),
                'today': fetch('today'),
                'default_locktime': fetch('default_locktime'),
                'default_usage_count': fetch('default_usage_count')
            }, f, indent=4)
