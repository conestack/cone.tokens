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
from cone.tokens.model import TokenNode
from cone.tokens.token import Tokens
from datetime import datetime 
from node.utils import UNSET
from plumber import plumbing
from pyramid.i18n import TranslationStringFactory
from pyramid.view import view_config
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
            '#field:label:error:datetime',
            value=attrs.get('valid_from', UNSET),
            props={
                'label': 'Valid from',
                'datepicker': True,
                'locale': 'de',
                'persist': True
            }
        )
        form['valid_to'] = factory(
            '#field:label:error:datetime',
            value=attrs.get('valid_to', UNSET),
            props={
                'label': 'Valid to',
                'datepicker': True,
                'locale': 'de',
                'persist': True,
                'required': 'Valid to field cannot be empty'
            }
        )
        form['usage_count'] = factory(
            '#field:label:error:number',
            value=attrs.get('usage_count', UNSET),
            props={
                'label': 'Usage Count',
                'required': 'Usage Count field cannot be empty'
            }
        )
        form['lock_time'] = factory(
            '#field:label:error:number',
            value=attrs.get('lock_time', UNSET),
            props={
                'label': 'Lock Time',
                'required': 'Lock time field cannot be empty'
            }
        )
        form['save'] = factory(
            'submit',
            props={
                'action': 'save',
                'expression': True,
                'handler': self.save,
                'next': self.next,
                'label': 'Save'
            }
        )
        form['cancel'] = factory(
            'submit',
            props={
                'action': 'cancel',
                'expression': True,
                'skip': True,
                'next': self.next,
                'label': 'Cancel'
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


@tile(
    name='contents',
    interface=TokenNode,
    permission='view')
class TokenContainerTile(ContentsTile):
    ...


@view_config(
    name='token_add',
    accept='application/json',
    renderer='json',
    permission='add')
def token_add(model, request):
    result = request.response
    params = request.params
    result.content_type = 'application/json'
    if not request.method == 'POST':
        result = request.response
        result.status_code = 405
        result.json = {'reason': 'Method not allowed'}
        return result
    token_api = Tokens(request)
    token_uid = params.get('uuid') if params.get('uuid') else uuid.uuid4()
    valid_from = params.get('valid_from') if params.get('valid_from') else datetime.now()
    if not params.get('valid_to'):
        result.status_code = 400
        result.json = {'reason': 'No Param valid_to'}
        return result
    if not params.get('usage_count'):
        result.status_code = 400
        result.json = {'reason': 'No Param usage_count'}
        return result
    if not params.get('lock_time'):
        result.status_code = 400
        result.json = {'reason': 'No Param lock_time'}
        return result
    token_api.add(
        token_uid,
        params.get('valid_to'),
        params.get('usage_count'),
        params.get('lock_time'),
        valid_from=valid_from
    )
    result.status_code = 200
    result.json =  {'token_uid': token_uid}
    return result


@view_config(
    name='token_delete',
    accept='application/json',
    renderer='json',
    permission='delete')
def token_delete(model, request):
    result = request.response
    params = request.params
    result.content_type = 'application/json'
    if not request.method == 'POST':
        result = request.response
        result.status_code = 405
        result.json = {'reason': 'Method not allowed'}
        return result
    token_api = Tokens(request)
    if not params.get('uuid'):
        result.status_code = 400
        result.json = {'reason': 'No Param uuid'}
        return result
    token_uid = params.get('uuid')
    token_api.delete(token_uid)
    result.status_code = 200
    result.json =  {'token_uid': token_uid}
    return result


@view_config(
    name='token_edit',
    accept='application/json',
    renderer='json',
    permission='edit')
def token_edit(model, request):
    result = request.response
    params = request.params
    result.content_type = 'application/json'
    if not request.method == 'POST':
        result = request.response
        result.status_code = 405
        result.json = {'reason': 'Method not allowed'}
        return result
    token_api = Tokens(request)
    if not params.get('uuid'):
        result.status_code = 400
        result.json = {'reason': 'No Param uuid'}
        return result
    token_uid = params.get('uuid')
    valid_to = params.get('valid_to') if params.get('valid_to') else None
    usage_count = params.get('usage_count') if params.get('usage_count') else None
    lock_time = params.get('lock_time') if params.get('lock_time') else None
    valid_from = params.get('valid_from') if params.get('valid_from') else None
    token_api.update(
        token_uid,
        valid_to=valid_to,
        usage_count=usage_count,
        lock_time=lock_time,
        valid_from=valid_from
    )
    result.status_code = 200
    result.json = {'token_uid': token_uid}
    return result


@view_config(
    name='token_consume',
    accept='application/json',
    renderer='json',
    permission='view')
def token_consume(model, request):
    result = request.response
    params = request.params
    result.content_type = 'application/json'
    if not request.method == 'GET':
        result = request.response
        result.status_code = 405
        result.json = {'reason': 'Method not allowed'}
        return result
    token_api = Tokens(request)
    if not params.get('uuid'):
        result.status_code = 400
        result.json = {'reason': 'No Param uuid'}
        return result
    token_uid = params.get('uuid')
    consumed = token_api.consume(token_uid)
    if consumed:
        result.status_code = 200
        result.json = {'consumed': token_uid}
        return result
    else:
        result.status_code = 301
        return result
