from base64 import b64encode
from cone.app.browser.authoring import ContentAddForm
from cone.app.browser.authoring import ContentEditForm
from cone.app.browser.form import Form
from cone.app.browser.layout import ProtectedContentTile
from cone.app.browser.utils import make_url
from cone.app.browser.utils import request_property
from cone.app.utils import add_creation_metadata
from cone.app.utils import update_creation_metadata
from cone.sql import get_session
from cone.tile import tile
from cone.tokens.model import TokenNode
from cone.tokens.model import TokenRecord
from cone.tokens.settings import get_settings_node
from datetime import datetime
from node.utils import UNSET
from plumber import plumbing
from pyramid.i18n import TranslationStringFactory
from pyramid.response import Response
from pyramid.view import view_config
from yafowil.base import ExtractionError
from yafowil.base import factory
from yafowil.persistence import node_attribute_writer
import io
import json
import qrcode


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

    @property
    def token_settings(self):
        attrs = get_settings_node(self.model).attrs
        return json.dumps({
            'base_url': self.nodeurl,
            'timeranges': attrs
        })

    @request_property
    def qrcode(self):
        return b64_qr_code(self.model.attrs['value'])

    @property
    def lock_time_seconds(self):
        return f"{self.model.attrs.get('lock_time')} sec"

    @property
    def is_active(self):
        # check if token is active / valid, does not check lock time
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
        settings = get_settings_node(self.model)
        usage_count = attrs['usage_count']
        if usage_count is None:
            usage_count = settings.attrs['default_usage_count']
        form['usage_count'] = factory(
            '#field:number',
            value=usage_count,
            props={
                'label': _('usage_count', default='Usage Count'),
                'datatype': int,
                'emptyvalue': 0
            }
        )
        lock_time = attrs['lock_time']
        if lock_time is None:
            lock_time = settings.attrs['default_locktime']
        form['lock_time'] = factory(
            '#field:number',
            value=lock_time,
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
            value = str(self.model.uuid)
        self.model.attrs['value'] = value


@tile(name='addform', interface=TokenNode, permission='add')
@plumbing(ContentAddForm)
class TokenAddForm(TokenForm):

    def save(self, widget, data):
        super(TokenAddForm, self).save(widget, data)
        self.model.parent[str(self.model.uuid)] = self.model
        add_creation_metadata(self.request, self.model.attrs)
        self.model()


@tile(name='editform', interface=TokenNode, permission='edit')
@plumbing(ContentEditForm)
class TokenEditForm(TokenForm):

    def save(self, widget, data):
        super(TokenEditForm, self).save(widget, data)
        update_creation_metadata(self.request, self.model.attrs)
        self.model()
