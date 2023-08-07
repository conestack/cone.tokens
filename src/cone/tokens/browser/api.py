from cone.tokens.exceptions import TokenAPIError
from cone.tokens.exceptions import TokenLockTimeViolation
from cone.tokens.exceptions import TokenNotExists
from cone.tokens.exceptions import TokenTimeRangeViolation
from cone.tokens.exceptions import TokenUsageCountExceeded
from cone.tokens.exceptions import TokenValueError
from cone.tokens.model import TokenContainer
from cone.tokens.model import TokenNode
from cone.tokens.token import Tokens
from pyramid.view import view_config
import datetime
import dateutil.parser
import uuid


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
    except Exception as e:
        return dict(success=False,message=str(e))
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
    except Exception as e:
        return dict(success=False,message=str(e))
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
    except Exception as e:
        return dict(success=False,message=str(e))
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
    except Exception as e:
        return dict(success=False,message=str(e))
    return dict(success=True, consumed=consumed)
