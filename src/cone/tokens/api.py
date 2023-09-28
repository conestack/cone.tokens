from cone import sql
from cone.sql import get_session
from cone.sql import use_tm
from cone.tokens.exceptions import TokenLockTimeViolation
from cone.tokens.exceptions import TokenNotExists
from cone.tokens.exceptions import TokenTimeRangeViolation
from cone.tokens.exceptions import TokenUsageCountExceeded
from cone.tokens.exceptions import TokenValueError
from cone.tokens.model import TokenUsageRecord
from cone.tokens.model import TokenRecord
from datetime import datetime
from datetime import timedelta
from node.utils import UNSET
from node.utils import instance_property
from pyramid.i18n import TranslationStringFactory
from pyramid.threadlocal import get_current_request
import uuid


_ = TranslationStringFactory('cone.tokens')


class TokenAPI(object):

    def __init__(self, request=None):
       self.request = request

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        self.session.close()

    @instance_property
    def session(self):
        if self.request is None:
            return sql.session_factory()
        return get_session(self.request)

    def flush_or_commit(self):
        if use_tm() and self.request is not None:
            self.session.flush() # pragma: no cover
        else:
            self.session.commit()

    def get_token(self, token_uid):
        session = self.session
        token = session\
            .query(TokenRecord)\
            .filter(TokenRecord.uid == token_uid)\
            .one_or_none()
        if not token:
            raise TokenNotExists(token_uid)
        return token

    def query_token(self, value):
        session = self.session
        return session\
            .query(TokenRecord)\
            .filter(TokenRecord.value == value)\
            .one_or_none()

    def token_values(self, token_uids):
        session = self.session
        res = session\
            .query(TokenRecord.value)\
            .filter(TokenRecord.uid.in_(token_uids))\
            .all()
        return [it[0] for it in res]

    @property
    def _authenticated_userid(self):
        request = get_current_request()
        if request:
            return request.authenticated_userid

    def _log_usage(self, token_uid, token_value, error_code=None):
        record = TokenUsageRecord()
        record.uid = uuid.uuid4()
        record.token_uid = token_uid
        record.token_value = token_value
        record.timestamp = datetime.now()
        record.error_code = error_code
        record.user = self._authenticated_userid
        self.session.add(record)
        self.flush_or_commit()

    def consume(self, token_uid):
        token = self.get_token(token_uid)
        if token.usage_count == 0:
            exc = TokenUsageCountExceeded(token_uid)
            self._log_usage(token_uid, token.value, error_code=exc.error_code)
            raise exc
        now = datetime.now()
        if token.last_used:
            if token.last_used + timedelta(0, token.lock_time) > now:
                exc = TokenLockTimeViolation(token_uid)
                self._log_usage(token_uid, token.value, error_code=exc.error_code)
                raise exc
        valid_from = token.valid_from
        valid_to = token.valid_to
        if valid_from and now < valid_from:
            exc = TokenTimeRangeViolation(token_uid)
            self._log_usage(token_uid, token.value, error_code=exc.error_code)
            raise exc
        if valid_to and now > valid_to:
            exc = TokenTimeRangeViolation(token_uid)
            self._log_usage(token_uid, token.value, error_code=exc.error_code)
            raise exc
        if token.usage_count != -1:
            token.usage_count -= 1
        token.last_used = now
        self._log_usage(token_uid, token.value)
        return True

    def add(
        self,
        token_uid,
        value=None,
        valid_from=None,
        valid_to=None,
        usage_count=0,
        lock_time=0
    ):
        try:
            self.get_token(token_uid)
            raise TokenValueError(f'Token with uid {token_uid} already exists')
        except TokenNotExists:
            if valid_from and valid_to and valid_from >= valid_to:
                raise TokenValueError('valid_from must be before valid_to')
            if not value:
                value = str(token_uid)
            session = self.session
            token = TokenRecord()
            token.uid = token_uid
            token.value = value
            token.valid_from = valid_from
            token.valid_to = valid_to
            token.lock_time = lock_time
            token.usage_count = usage_count
            token.creator = self._authenticated_userid
            now = datetime.now()
            token.created = now
            token.modified = now
            session.add(token)
            self.flush_or_commit()

    def update(
        self,
        token_uid,
        value=UNSET,
        valid_from=UNSET,
        valid_to=UNSET,
        usage_count=UNSET,
        lock_time=UNSET
    ):
        token = self.get_token(token_uid)
        session = self.session
        if value is not UNSET and value != token.value:
            existing = self.query_token(value)
            if existing and existing.uid != token_uid:
                raise TokenValueError('Given value already used by another token')
            token.value = value
        if valid_from is not UNSET:
            token.valid_from = valid_from
        if valid_to is not UNSET:
            token.valid_to = valid_to
        if lock_time is not UNSET:
            token.lock_time = lock_time
        if usage_count is not UNSET:
            token.usage_count = usage_count
        if token.valid_from and token.valid_to and token.valid_from >= token.valid_to:
            session.rollback()
            raise TokenValueError('valid_from must be before valid_to')
        token.modified = datetime.now()
        self.flush_or_commit()

    def delete(self, token_uid):
        session = self.session
        token = self.get_token(token_uid)
        session.delete(token)
        self.flush_or_commit()
