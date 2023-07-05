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
    
    def __get_token(self):
        session = self.session
        token = session\
            .query(TokenRecord)\
            .filter(TokenRecord.uid == self.token_uid)\
            .first()
        if not token:
            raise TokenNotExists(self.token_uid)
        return token
    
    def consume(self):
        session = self.session
        existing = self.__get_token()
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
    
    def add(self,valid_to,usage_count,lock_time,valid_from=datetime.now()):
        session = self.session
        token = TokenRecord()
        token.uid = self.token_uid
        token.valid_from = valid_from
        token.valid_to = valid_to
        token.lock_time = lock_time
        token.usage_count = usage_count
        session.add(token)
        session.commit()

    def update(self,valid_from=None,valid_to=None,usage_count=None,lock_time=None):
        token = self.__get_token()
        session = self.session
        if valid_from:
            token.valid_from = valid_from
        if valid_to:
            token.valid_to = valid_to
        if lock_time:
            token.lock_time = lock_time
        if usage_count:
            token.usage_count = usage_count
        session.commit()
    
    def delete(self):
        session = self.session
        token = self.__get_token()
        session.delete(token)
        session.commit()