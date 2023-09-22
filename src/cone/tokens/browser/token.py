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
from cone.sql import get_session
from cone.tile import Tile
from cone.tile import tile
from cone.tile import tile
from cone.tokens.model import TokenNode
from cone.tokens.model import TokenRecord
from datetime import datetime
from datetime import timedelta
from node.utils import UNSET
from plumber import plumbing
from pyramid.i18n import TranslationStringFactory
from pyramid.response import Response
from pyramid.view import view_config
from yafowil.base import ExtractionError
from yafowil.base import factory
from yafowil.persistence import node_attribute_writer
import io
import qrcode
import uuid


_ = TranslationStringFactory('cone.tokens')


def qr_code(value):
    img = qrcode.make(value)
    data = io.BytesIO()
    img.save(data, format='png')
    return data.getvalue()


def b64_qr_code(value):
    return 'data:image/png;base64,' + b64encode(qr_code(value)).decode('utf-8')


@view_config(name='qr_code', context=TokenNode, permission='view')
def download_qr_code(model, request):
    response = Response(
        content_type='image/png',
        content_disposition=f'attachment;filename={model.name}.png'
    )
    response.body = qr_code(model.attrs['value'])
    return response


@tile(
    name='content',
    path='templates/token.pt',
    interface=TokenNode,
    permission='view')
class TokenContent(ProtectedContentTile):

    @request_property
    def qrcode(self):
        return b64_qr_code(self.model.attrs['value'])

    @property
    def lock_time_seconds(self):
        return f"{self.model.attrs.get('lock_time')} sec"

    @property
    def is_active(self):
        #check if token is active / valid,  doesnt check locktime
        attrs = self.model.attrs
        if attrs.get('usage_count') == 0:
            return False
        if attrs.get('valid_to') and datetime.now() > attrs.get('valid_to'):
            return False
        if attrs.get('valid_from') and datetime.now() < attrs.get('valid_from'):
            return False
        return True

    @property
    def active_label(self):
        return 'Active' if self.is_active else 'Inactive'

    @property
    def cssclass(self):
        return 'btn-success' if self.is_active else 'btn-danger'

    def format_date(self, value):
        if isinstance(value, datetime):
            return value.strftime('%d.%m.%Y, %H:%M:%S')
        return 'Unlimited'


@tile(name='add_duration', interface=TokenNode, permission='edit')
class AddDuration(Tile):

    # action event to reload the page and update the tokens valid_to and valid_from
    def render(self):
        event = AjaxEvent(
            target=make_url(self.request, node=self.model),
            name='contextchanged',
            selector='#layout'
        )
        current_time = datetime.now()
        if self.request.params.get('duration') == 'morning':
            if current_time.hour < 12:
                self.model.attrs['valid_from'] = current_time.replace(
                    hour=6,
                    minute=0,
                    second=0,
                    microsecond=0
                )
                self.model.attrs['valid_to'] = current_time.replace(
                    hour=12,
                    minute=0,
                    second=0,
                    microsecond=0
                )
            else: # tomorrow
                self.model.attrs['valid_from'] = current_time.replace(
                    hour=6,
                    minute=0,
                    second=0,
                    microsecond=0
                ) + timedelta(days=1)
                self.model.attrs['valid_to'] = current_time.replace(
                    hour=12,
                    minute=0,
                    second=0,
                    microsecond=0
                ) + timedelta(days=1)
        if self.request.params.get('duration') == 'day':
            self.model.attrs['valid_from'] = current_time.replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0
            )
            self.model.attrs['valid_to'] = current_time.replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0
            ) + timedelta(days=1)
        if self.request.params.get('duration') == 'week':
            self.model.attrs['valid_from'] = current_time.replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0
            ) - timedelta(days=current_time.weekday())
            self.model.attrs['valid_to'] = current_time.replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0
            ) + timedelta(days=7-current_time.weekday())
        ajax_continue(self.request, [event])
        return u''


@tile(name='add_use', interface=TokenNode, permission='edit')
class AddUse(Tile):

    # action event to reload the page and update the tokens usage_count
    def render(self):
        event = AjaxEvent(
            target=make_url(self.request, node=self.model),
            name='contextchanged',
            selector='#layout'
        )
        if self.request.params.get('amount') == '-1':
            self.model.attrs['usage_count'] = -1
        else:
            self.model.attrs['usage_count'] += int(self.request.params.get('amount'))
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
        extracted = data.extracted
        if extracted is UNSET:
            return extracted
        valid_from = data.fetch('tokenform.valid_from').extracted
        if valid_from and extracted:
            if valid_from >= extracted:
                raise ExtractionError(_(
                    'timerange_error',
                    default='Valid from date must be before valid to date'
                ))
        return extracted

    def value_extractor(self, widget, data):
        extracted = data.extracted
        if not extracted:
            return extracted
        session = get_session(self.request)
        existing_value = session.query(TokenRecord) \
            .filter(TokenRecord.value == extracted) \
            .filter(TokenRecord.uid != self.model.record.uid) \
            .one_or_none()
        if existing_value:
            raise ExtractionError(_(
                'value_already_used',
                default='Value already used by another token'
            ))
        return extracted

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
        form['value'] = factory(
            '#field:*value:text',
            value=attrs.get('value', UNSET),
            props={
                'label': _('value', default='Value'),
                'persist': False
            },
            custom={
                'value': {
                    'extractors': [self.value_extractor]
                }
            }
        )
        form['valid_from'] = factory(
            '#field:datetime',
            value=attrs.get('valid_from', UNSET),
            props={
                'label': _('valid_from', default='Valid from'),
                'datepicker': True,
                'timepicker': True,
                'time': True,
                'locale': 'de',
                'persist': True
            }
        )
        form['valid_to'] = factory(
            '#field:*valid_to:datetime',
            value=attrs.get('valid_to', UNSET),
            props={
                'label': _('valid_to', default='Valid to'),
                'datepicker': True,
                'timepicker': True,
                'time': True,
                'locale': 'de',
                'persist': True
            },
            custom={
                'valid_to': {
                    'extractors': [self.timerange_extractor]
                }
            }
        )
        form['usage_count'] = factory(
            '#field:number',
            value=attrs.get('usage_count', UNSET),
            props={
                'label': _('usage_count', default='Usage Count'),
                'datatype': int,
                'emptyvalue': -1
            }
        )
        form['lock_time'] = factory(
            '#field:number',
            value=attrs.get('lock_time', UNSET),
            props={
                'label': _('lock_time', default='Lock Time'),
                'datatype': int,
                'emptyvalue': 0
            }
        )
        form['save'] = factory(
            'submit',
            props={
                'action': 'save',
                'expression': True,
                'handler': self.save,
                'next': self.next,
                'label': _('save', default='Save')
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
        value = data.fetch('tokenform.value').extracted
        # token uid gets used as value if no value given
        if not value:
            value = self.token_uid
        self.model.attrs['value'] = value


@tile(name='addform', interface=TokenNode, permission='add')
@plumbing(ContentAddForm)
class TokenAddForm(TokenForm):

    @request_property
    def token_uid(self):
        return str(uuid.uuid4())

    def save(self, widget, data):
        super(TokenAddForm, self).save(widget, data)
        self.model.parent[self.token_uid] = self.model
        add_creation_metadata(self.request, self.model.attrs)
        self.model()


@tile(name='editform', interface=TokenNode, permission='edit')
@plumbing(ContentEditForm)
class TokenEditForm(TokenForm):

    @property
    def token_uid(self):
        return self.model.name

    def save(self, widget, data):
        super(TokenEditForm, self).save(widget, data)
        update_creation_metadata(self.request, self.model.attrs)
        self.model()
