from cone.sql import get_session
from cone.sql import use_tm
from cone.tokens.exceptions import TokenLockTimeViolation
from cone.tokens.exceptions import TokenValueError
from cone.tokens.exceptions import TokenNotExists
from cone.tokens.exceptions import TokenTimeRangeViolation
from cone.tokens.exceptions import TokenUsageCountExceeded
from cone.tokens.model import TokenRecord
from datetime import datetime 
from datetime import timedelta
from pyramid.i18n import TranslationStringFactory


_ = TranslationStringFactory('cone.tokens')


class Tokens(object):

    def __init__(self, request):
       self.request = request

    @property
    def session(self):
        return get_session(self.request)

    def _get_token(self,token_uid):
        session = self.session
        token = session\
            .query(TokenRecord)\
            .filter(TokenRecord.uid == token_uid)\
            .one_or_none()
        if not token:
            raise TokenNotExists(token_uid)
        return token

    def consume(self, token_uid):
        session = self.session
        existing = self._get_token(token_uid)
        if existing.usage_count == 0:
            raise TokenUsageCountExceeded(token_uid)
        current_time = datetime.now()
        if existing.last_used:
            if existing.last_used + timedelta(0, existing.lock_time) > current_time:
                raise TokenLockTimeViolation(token_uid)
        if current_time > existing.valid_to or current_time < existing.valid_from:
            raise TokenTimeRangeViolation(token_uid)
        if existing.usage_count != -1:
            existing.usage_count -= 1
        existing.last_used = current_time
        if use_tm():
            session.flush()
        else:
            session.commit()
        return True

    def add(
        self,
        token_uid,
        valid_from,
        valid_to,
        usage_count,
        lock_time
    ):
        session = self.session
        if valid_from >= valid_to:
            raise TokenValueError('valid_from must be before valid_to')
        token = TokenRecord()
        token.uid = token_uid
        token.valid_from = valid_from
        token.valid_to = valid_to
        token.lock_time = lock_time
        token.usage_count = usage_count
        session.add(token)
        if use_tm():
            session.flush()
        else:
            session.commit()

    def update(
        self,
        token_uid,
        valid_from=None,
        valid_to=None,
        usage_count=None,
        lock_time=None
    ):
        token = self._get_token(token_uid)
        session = self.session
        if valid_from:
            token.valid_from = valid_from
        if valid_to:
            token.valid_to = valid_to
        if lock_time:
            token.lock_time = lock_time
        if usage_count:
            token.usage_count = usage_count
        if token.valid_from >= token.valid_to:
            raise TokenValueError('valid_from must be before valid_to')
        if use_tm():
            session.flush()
        else:
            session.commit()

    def delete(self, token_uid):
        session = self.session
        token = self._get_token(token_uid)
        session.delete(token)
        if use_tm():
            session.flush()
        else:
            session.commit()
