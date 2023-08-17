from base64 import b64encode
from cone.app.browser.ajax import AjaxEvent
from cone.app.browser.ajax import ajax_continue
from cone.app.browser.authoring import ContentAddForm
from cone.app.browser.authoring import ContentEditForm
from cone.app.browser.form import Form
from cone.app.browser.layout import ProtectedContentTile
from cone.app.browser.utils import make_url
from cone.app.browser.utils import request_property
from cone.app.utils import add_creation_metadata
from cone.app.utils import update_creation_metadata
from cone.tile import Tile
from cone.tile import tile
from cone.tile import tile
from cone.tokens.exceptions import TokenValueError
from cone.tokens.model import TokenNode
from node.utils import UNSET
from plumber import plumbing
from pyramid.i18n import TranslationStringFactory
from yafowil.base import factory
from yafowil.persistence import node_attribute_writer
import io
import qrcode
import uuid

_ = TranslationStringFactory('cone.tokens')


@tile(
    name='content',
    path='templates/token.pt',
    interface=TokenNode,
    permission='view')
class TokenTile(ProtectedContentTile):

    @request_property
    def stream_qrcode_token(self):
        img = qrcode.make(self.model.attrs['uid'])
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = b64encode(img_byte_arr.getvalue()).decode('utf-8')
        qr_src = 'data:image/png;base64,' + img_byte_arr
        return qr_src
    
    @property
    def lock_time_seconds(self):
        return f"{self.model.attrs.get('lock_time')} sec"
    
    def active_toggle(self):
        print('active_toggle')
        self.model.attrs['active'] = not self.model.attrs['active']


@tile(name='toggle_Action', permission='view')
class ExampleAction(Tile):

    def render(self):
        event = AjaxEvent(
            target=make_url(self.request, node=self.model),
            name='contextchanged',
            selector='#layout'
        )
        self.model.attrs['active'] = not self.model.attrs['active']
        ajax_continue(self.request, [event])
        return u''


class TokenForm(Form):
    form_name = 'tokenform'

    @property
    def form_action(self):
        return make_url(
            self.request,
            node=self.model,
            resource=self.action_resource
        )

    def timerange_extractor(self, widget, data):
        valid_from = data.fetch('tokenform.valid_from').extracted
        valid_to = data.fetch('tokenform.valid_to').extracted
        if not valid_from or not valid_to:
            return
        if valid_from >= valid_to:
            raise TokenValueError('valid_from must be before valid_to')

    def prepare(self):
        form = self.form = factory(
            '#form',
            name=self.form_name,
            props={
                'action': self.form_action,
                'persist_writer': node_attribute_writer
            }
        )
        attrs = self.model.attrs
        form['valid_from'] = factory(
            '#field:datetime',
            value=attrs.get('valid_from', UNSET),
            props={
                'label': _('valid_from', default='Valid from'),
                'datepicker': True,
                'locale': 'de',
                'persist': True
            }
        )
        form['valid_to'] = factory(
            '#field:datetime',
            value=attrs.get('valid_to', UNSET),
            props={
                'label': _('valid_to', default='Valid to'),
                'datepicker': True,
                'locale': 'de',
                'persist': True
            }
        )
        form['usage_count'] = factory(
            '#field:number',
            value=attrs.get('usage_count', UNSET),
            props={
                'label': _('usage_count', default='Usage Count'),
                'datatype': 'integer',
                'emptyvalue': -1
            }
        )
        form['lock_time'] = factory(
            '#field:number',
            value=attrs.get('lock_time', UNSET),
            props={
                'label': _('lock_time', default='Lock Time'),
                'datatype': 'integer',
                'emptyvalue': 0
            }
        )
        form['save'] = factory(
            'submit:*timerange_extractor',
            props={
                'action': 'save',
                'expression': True,
                'handler': self.save,
                'next': self.next,
                'label': _('save', default='Save')
            },
            custom={
                'timerange_extractor': {
                    'extractors': [self.timerange_extractor]
                }
            }
        )
        form['cancel'] = factory(
            'submit',
            props={
                'action': 'cancel',
                'expression': True,
                'skip': True,
                'next': self.next,
                'label': _('cancel', default='Cancel')
            }
        )

    def save(self, widget, data):
        data.write(self.model)


@tile(name='addform', interface=TokenNode, permission='add')
@plumbing(ContentAddForm)
class TokenAddForm(TokenForm):

    def save(self, widget, data):
        super(TokenAddForm, self).save(widget, data) 
        self.model.parent[str(uuid.uuid4())] = self.model
        add_creation_metadata(self.request, self.model.attrs)
        self.model()


@tile(name='editform', interface=TokenNode, permission='edit')
@plumbing(ContentEditForm)
class TokenEditForm(TokenForm):

    def save(self, widget, data):
        super(TokenEditForm, self).save(widget, data)
        update_creation_metadata(self.request, self.model.attrs)
        self.model()
