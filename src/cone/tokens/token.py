from cone.sql import get_session
from cone.tokens.exceptions import TokenLockTimeViolation
from cone.tokens.exceptions import TokenNotExists
from cone.tokens.exceptions import TokenTimeRangeViolation
from cone.tokens.exceptions import TokenUsageCountExceeded
from cone.tokens.model import TokenRecord
from datetime import datetime 
from datetime import timedelta
from pyramid.i18n import TranslationStringFactory
from typing import Any

_ = TranslationStringFactory('cone.tokens')


class Tokens(object):
    """cone.tokens API
    """

    def __init__(self, request, token_uid):
       self.request = request
       self.token_uid = token_uid
    
    @property
    def session(self):
        return get_session(self.request)
    
    def __call__(self):
        session = self.session
        existing = session\
            .query(TokenRecord)\
            .filter(TokenRecord.uid == self.token_uid)\
            .first()
        if not existing:
            raise TokenNotExists(self.token_uid)
        if existing.usage_count == 0:
            raise TokenUsageCountExceeded(self.token_uid)
        current_time = datetime.now()
        if existing.last_used + timedelta(0, existing.lock_time) > current_time:
            raise TokenLockTimeViolation(self.token_uid)
        if current_time > existing.valid_to or current_time < existing.valid_from:
            raise TokenTimeRangeViolation(self.token_uid)
        if existing.usage_count != -1:
            existing.usage_count -= 1
        existing.last_used = current_time
        session.commit()
        return True
