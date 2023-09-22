from cone.tokens.api import TokenAPI
from cone.tokens.exceptions import TokenException
from cone.tokens.exceptions import TokenValueError
from cone.tokens.model import TokenContainer
from cone.tokens.model import TokenNode
from pyramid.view import view_config
import dateutil.parser
import uuid


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


@view_config(
    name='consume_token',
    request_method='GET',
    accept='application/json',
    renderer='json',
    context=TokenNode,
    permission='view')
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
    api = TokenAPI(request)
    uid = uuid.uuid4()
    kw = dict()
    read_string(request, 'value', kw)
    try:
        read_datetime(request, 'valid_from', kw)
        read_datetime(request, 'valid_to', kw)
        read_int(request, 'usage_count', kw, default=-1)
        read_int(request, 'lock_time', kw)
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
        read_int(request, 'usage_count', kw, default=-1)
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
