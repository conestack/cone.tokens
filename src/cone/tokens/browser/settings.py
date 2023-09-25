from cone.app.browser.authoring import ContentEditForm
from cone.app.browser.form import Form
from cone.app.browser.layout import ProtectedContentTile
from cone.app.browser.settings import SettingsBehavior
from cone.app.browser.utils import make_url
from cone.tile import tile
from cone.tokens.settings import TimeSettings
from node.utils import UNSET
from plumber import plumbing
from pyramid.i18n import TranslationStringFactory
from yafowil.base import ExtractionError
from yafowil.base import factory
from yafowil.persistence import node_attribute_writer
import json


_ = TranslationStringFactory('cone.ugm')


@tile(
    name='content',
    path='templates/time_settings.pt',
    interface=TimeSettings,
    permission='manage')
class TimeSettingsContent(ProtectedContentTile):
    pass


# XXX permission
@tile(name='editform', interface=TimeSettings, permission='edit')
@plumbing(SettingsBehavior, ContentEditForm)
class TimeSettingsForm(Form):
    action_resource = u'edit'
    form_name = 'timeform'

    @property
    def message_factory(self):
        return _

    def prepare(self):
        action = make_url(
                self.request,
                node=self.model,
                resource=self.action_resource)
        form = self.form = factory('#form', name=self.form_name, props={
            'action': action,
            'persist_writer': node_attribute_writer
        })
        form['morning'] = factory(
            '#field:compound',
            props={
                'label': 'Morning'
            }
        )
        form['morning.start'] = factory(
            '#field:time',
            value=UNSET,
            props={
                'label': 'Start',
                'timepicker': True,
                'time': True
        })
        form['morning.end'] = factory(
            '#field:time',
            value=UNSET,
            props={
                'label': 'End',
                'timepicker': True,
                'time': True
        })
        form['afternoon'] = factory(
            '#field:compound',
            props={
                'label': 'Afternoon'
            }
        )
        form['afternoon.start'] = factory(
            '#field:time',
            value=UNSET,
            props={
                'label': 'Start',
                'timepicker': True,
                'time': True
        })
        form['afternoon.end'] = factory(
            '#field:time',
            value=UNSET,
            props={
                'label': 'End',
                'timepicker': True,
                'time': True
        })
        form['today'] = factory(
            '#field:compound',
            props={
                'label': 'Today'
            }
        )
        form['today.start'] = factory(
            '#field:time',
            value=UNSET,
            props={
                'label': 'Start',
                'timepicker': True,
                'time': True
        })
        form['today.end'] = factory(
            '#field:time',
            value=UNSET,
            props={
                'label': 'End',
                'timepicker': True,
                'time': True
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
        # XXX: custom extractor for compound
        morning = data.fetch('timeform.%s' % 'morning').extracted

        with open('time.json') as f:
            dat = json.load(f)
        dat['morning'] = morning
        with open("time.json", "w") as f:
            json.dump(dat, f)
