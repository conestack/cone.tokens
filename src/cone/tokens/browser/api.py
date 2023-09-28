from cone.tokens.api import TokenAPI
from cone.tokens.exceptions import TokenException
from cone.tokens.exceptions import TokenValueError
from cone.tokens.model import TokenContainer
from cone.tokens.model import TokenNode
from cone.tokens.settings import get_settings_node
from pyramid.i18n import get_localizer
from pyramid.i18n import TranslationStringFactory
from pyramid.view import view_config
import dateutil.parser
import json
import uuid


_ = TranslationStringFactory('cone.tokens')


def read_string(request, param, kw, default=None):
    if param in request.params:
        value = request.params[param]
        if not value:
            value = default
        kw[param] = value


def read_datetime(request, param, kw, default=None):
    if param in request.params:
        value = request.params[param]
        if not value:
            kw[param] = default
        else:
            try:
                kw[param] = dateutil.parser.isoparse(value)
            except ValueError:
                raise TokenValueError(f'{param}: invalid datetime format')


def read_int(request, param, kw, default=0):
    if param in request.params:
        value = request.params[param]
        if not value:
            kw[param] = default
        else:
            try:
                kw[param] = int(request.params[param])
            except ValueError:
                raise TokenValueError(f'{param}: value is no integer')


def format_datetime(dt):
    if not dt:
        return None
    return dt.isoformat()


@view_config(
    name='query_token',
    request_method='GET',
    accept='application/json',
    renderer='json',
    context=TokenContainer,
    permission='view')
def query_token(model, request):
    api = TokenAPI(request)
    try:
        value = request.params['value']
        token = api.query_token(value)
        if not token:
            return dict(success=True, token=None)
        return dict(
            success=True,
            token=dict(
                uid=str(token.uid),
                value=token.value,
                last_used=format_datetime(token.last_used),
                valid_from=format_datetime(token.valid_from),
                valid_to=format_datetime(token.valid_to),
                usage_count=token.usage_count,
                lock_time=token.lock_time,
                creator=token.creator,
                created=format_datetime(token.created),
                modified=format_datetime(token.modified)
            )
        )
    except KeyError:
        return dict(success=False, message='Missing ``value`` parameter')
    except Exception as e:
        return dict(success=False, message=str(e))


@view_config(
    name='consume_token',
    request_method='GET',
    accept='application/json',
    renderer='json',
    context=TokenNode,
    permission='view')  # XXX: ``consume`` permission
def consume_token(model, request):
    api = TokenAPI(request)
    uid = uuid.UUID(model.name)
    try:
        consumed = api.consume(uid)
    except TokenException as e:
        return e.as_json()
    except Exception as e:
        return dict(success=False, message=str(e))
    return dict(success=True, consumed=consumed)


@view_config(
    name='add_token',
    request_method='POST',
    accept='application/json',
    renderer='json',
    context=TokenContainer,
    permission='add')
def add_token(model, request):
    settings = get_settings_node(model)
    api = TokenAPI(request)
    uid = uuid.uuid4()
    kw = dict()
    read_string(request, 'value', kw)
    try:
        read_datetime(request, 'valid_from', kw)
        read_datetime(request, 'valid_to', kw)
        read_int(
            request,
            'usage_count',
            kw,
            default=settings.attrs['default_usage_count']
        )
        read_int(
            request,
            'lock_time',
            kw,
            default=settings.attrs['default_locktime']
        )
    except TokenValueError as e:
        return e.as_json()
    try:
        api.add(uid, **kw)
    except TokenException as e:
        return e.as_json()
    except Exception as e:
        return dict(success=False, message=str(e))
    return dict(success=True, token_uid=str(uid))


@view_config(
    name='delete_tokens',
    request_method='POST',
    accept='application/json',
    renderer='json',
    context=TokenContainer,
    permission='delete')
def delete_tokens(model, request):
    api = TokenAPI(request)
    token_uids = request.params.get('token_uids', None)
    if not token_uids:
        return
    token_uids = json.loads(token_uids)
    token_count = len(token_uids)
    for t_uid in token_uids:
        uid = uuid.UUID(t_uid)
        try:
            api.delete(uid)
        except Exception as e:
            return dict(success=False, message=str(e))
    ts = _(
        'deleted_tokens',
        default='Successfully deleted ${count} Tokens.',
        mapping={'count': token_count}
    )
    localizer = get_localizer(request)
    message = localizer.translate(ts)
    return dict(success=True, message=message)


@view_config(
    name='update_token',
    request_method='POST',
    accept='application/json',
    renderer='json',
    context=TokenNode,
    permission='edit')
def update_token(model, request):
    api = TokenAPI(request)
    uid = uuid.UUID(model.name)
    kw = dict()
    read_string(request, 'value', kw)
    try:
        read_datetime(request, 'valid_from', kw)
        read_datetime(request, 'valid_to', kw)
        read_int(request, 'usage_count', kw)
        read_int(request, 'lock_time', kw)
    except TokenValueError as e:
        return e.as_json()
    try:
        api.update(uid, **kw)
    except TokenException as e:
        return e.as_json()
    except Exception as e:
        return dict(success=False, message=str(e))
    return dict(success=True)


@view_config(
    name='delete_token',
    request_method='POST',
    accept='application/json',
    renderer='json',
    context=TokenNode,
    permission='delete')
def delete_token(model, request):
    api = TokenAPI(request)
    uid = uuid.UUID(model.name)
    try:
        api.delete(uid)
    except Exception as e:
        return dict(success=False, message=str(e))
    return dict(success=True)
