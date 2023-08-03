from base64 import b64encode
from cone.app.browser.authoring import ContentAddForm
from cone.app.browser.authoring import ContentEditForm
from cone.app.browser.contents import ContentsTile
from cone.app.browser.form import Form
from cone.app.browser.layout import ProtectedContentTile
from cone.app.browser.utils import make_url
from cone.app.browser.utils import request_property
from cone.app.utils import add_creation_metadata
from cone.app.utils import update_creation_metadata
from cone.tile import tile
from cone.tokens.exceptions import TokenLockTimeViolation, TokenNotExists, TokenTimeRangeViolation, TokenUsageCountExceeded, TokenValueError
from cone.tokens.model import TokenNode
from cone.tokens.model import TokenContainer
from cone.tokens.token import Tokens
from node.utils import UNSET
from plumber import plumbing
from pyramid.i18n import TranslationStringFactory
from pyramid.i18n import get_localizer
from pyramid.view import view_config
from yafowil.base import factory
from yafowil.persistence import node_attribute_writer
import datetime
import dateutil.parser
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


class TokenForm(Form):
    form_name = 'tokenform'

    @property
    def form_action(self):
        return make_url(
            self.request,
            node=self.model,
            resource=self.action_resource
        )

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
                'required': _(
                    'valid_to_required',
                    default='Valid to field cannot be empty'
                ),
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
                'required': _(
                    'usage_count_required',
                    default='Usage Count field cannot be empty'
                )
            }
        )
        form['lock_time'] = factory(
            '#field:number',
            value=attrs.get('lock_time', UNSET),
            props={
                'label': _('lock_time', default='Lock Time'),
                'required': _(
                    'lock_time_required',
                    default='Lock time field cannot be empty'
                )
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

    def next(self, request):
        # method stub for tests
        ...


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


class TokenAPIError(Exception):

    def __init__(self, message):
        self.message = message

    def as_json(self):
        return dict(success=False, message=self.message)


def get_datetime(request, name, now_when_missing=False):
    # dateutil.parser.isoparse(datetime.datetime.now().isoformat())
    try:
        return dateutil.parser.isoparse(request.params[name])
    except KeyError:
        if now_when_missing:
            return datetime.datetime.now()
        raise TokenAPIError(f'`{name}` missing on request')
    except ValueError:
        raise TokenAPIError('Invalid datetime format')


def get_int(request, name):
    try:
        return int(request.params[name])
    except KeyError:
        raise TokenAPIError(f'`{name}` missing on request')
    except ValueError:
        raise TokenAPIError('Value is no integer')


@view_config(
    name='add_token',
    request_method='POST',
    accept='application/json',
    renderer='json',
    context=TokenContainer,
    permission='add')
def add_token(model, request):
    token_api = Tokens(request)
    token_uid = uuid.uuid4()
    valid_from = get_datetime(request, 'valid_from', now_when_missing=True)
    try:
        valid_to = get_datetime(request, 'valid_to')
    except TokenAPIError as e:
        return e.as_json()
    try:
        usage_count = get_int(request, 'usage_count')
    except TokenAPIError as e:
        return e.as_json()
    try:
        lock_time = get_int(request, 'lock_time')
    except TokenAPIError as e:
        return e.as_json()
    try:
        token_api.add(
            token_uid,
            valid_from,
            valid_to,
            usage_count,
            lock_time,
        )
    except TokenValueError as e:
        return e.as_json()
    return dict(success=True, token_uid=str(token_uid))


@view_config(
    name='delete_token',
    request_method='POST',
    accept='application/json',
    renderer='json',
    context=TokenNode,
    permission='delete')
def delete_token(model, request):
    token_api = Tokens(request)
    token_uid = uuid.UUID(model.name)
    try:
        token_api.delete(token_uid)
    except TokenNotExists as e:
        return e.as_json()
    return dict(success=True)


@view_config(
    name='edit_token',
    request_method='POST',
    accept='application/json',
    renderer='json',
    context=TokenNode,
    permission='edit')
def edit_token(model, request):
    token_api = Tokens(request)
    token_uid = uuid.UUID(model.name)
    try:
        valid_from = get_datetime(request, 'valid_from')
    except TokenAPIError as e:
        return e.as_json()
    try:
        valid_to = get_datetime(request, 'valid_to')
    except TokenAPIError as e:
        return e.as_json()
    try:
        usage_count = get_int(request, 'usage_count')
    except TokenAPIError as e:
        return e.as_json()
    try:
        lock_time = get_int(request, 'lock_time')
    except TokenAPIError as e:
        return e.as_json()
    try:
        token_api.update(
            token_uid,
            valid_to=valid_to,
            usage_count=usage_count,
            lock_time=lock_time,
            valid_from=valid_from
        )
    except TokenValueError as e:
        return e.as_json()
    except TokenNotExists as e:
        return e.as_json()
    return dict(success=True)


@view_config(
    name='consume_token',
    request_method='GET',
    accept='application/json',
    renderer='json',
    context=TokenNode,
    permission='view')
def consume_token(model, request):
    token_api = Tokens(request)
    token_uid = uuid.UUID(model.name)
    try:
        consumed = token_api.consume(token_uid)
    except TokenUsageCountExceeded as e:
        return e.as_json()
    except TokenLockTimeViolation as e:
        return e.as_json()
    except TokenTimeRangeViolation as e:
        return e.as_json()
    except TokenNotExists as e:
        return e.as_json()
    return dict(success=True, consumed=consumed)
