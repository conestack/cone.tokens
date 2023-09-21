from cone.sql import get_session
from cone.sql import use_tm
from cone.tokens.exceptions import TokenLockTimeViolation
from cone.tokens.exceptions import TokenNotExists
from cone.tokens.exceptions import TokenTimeRangeViolation
from cone.tokens.exceptions import TokenUsageCountExceeded
from cone.tokens.exceptions import TokenValueError
from cone.tokens.model import TokenRecord
from datetime import datetime 
from datetime import timedelta
from node.utils import UNSET
from pyramid.i18n import TranslationStringFactory


_ = TranslationStringFactory('cone.tokens')


class TokenAPI(object):

    def __init__(self, request):
       self.request = request

    @property
    def session(self):
        return get_session(self.request)

    def _get_token(self, token_uid):
        session = self.session
        token = session\
            .query(TokenRecord)\
            .filter(TokenRecord.uid == token_uid)\
            .one_or_none()
        if not token:
            raise TokenNotExists(token_uid)
        return token

    def _query_token(self, value):
        session = self.session
        return session\
            .query(TokenRecord)\
            .filter(TokenRecord.value == value)\
            .one_or_none()

    def consume(self, token_uid):
        session = self.session
        token = self._get_token(token_uid)
        if token.usage_count == 0:
            raise TokenUsageCountExceeded(token_uid)
        now = datetime.now()
        if token.last_used:
            if token.last_used + timedelta(0, token.lock_time) > now:
                raise TokenLockTimeViolation(token_uid)
        valid_from = token.valid_from
        valid_to = token.valid_to
        if valid_from and now < valid_from:
            raise TokenTimeRangeViolation(token_uid)
        if valid_to and now > valid_to:
            raise TokenTimeRangeViolation(token_uid)
        if token.usage_count != -1:
            token.usage_count -= 1
        token.last_used = now
        if use_tm():
            session.flush() # pragma: no cover
        else:
            session.commit()
        return True

    def add(
        self,
        token_uid,
        value=None,
        valid_from=None,
        valid_to=None,
        usage_count=-1,
        lock_time=0
    ):
        try:
            self._get_token(token_uid)
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
            session.add(token)
            if use_tm():
                session.flush() # pragma: no cover
            else:
                session.commit()

    def update(
        self,
        token_uid,
        value=UNSET,
        valid_from=UNSET,
        valid_to=UNSET,
        usage_count=UNSET,
        lock_time=UNSET
    ):
        token = self._get_token(token_uid)
        session = self.session
        if value is not UNSET and value != token.value:
            existing = self._query_token(value)
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
            raise TokenValueError('valid_from must be before valid_to')
        if use_tm():
            session.flush() # pragma: no cover
        else:
            session.commit()

    def delete(self, token_uid):
        session = self.session
        token = self._get_token(token_uid)
        session.delete(token)
        if use_tm():
            session.flush() # pragma: no cover
        else:
            session.commit()
