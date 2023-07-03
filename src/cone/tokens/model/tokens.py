from cone.sql import get_session
from cone.sql import SQLBase
from cone.sql.model import GUID
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import INTEGER
from pyramid.i18n import TranslationStringFactory
import decimal
import uuid
from datetime import datetime, timedelta

_ = TranslationStringFactory('cone.tokens')


class TokenRecord(SQLBase):
    __tablename__ = 'tokens'

    uid = Column(GUID, primary_key=True)
    last_used = Column(DateTime)
    valid_from = Column(DateTime)
    valid_to = Column(DateTime)
    usage_count = Column(INTEGER)
    lock_time = Column(INTEGER) # in seconds


class Tokens(object):
    """cone.tokens API
    """

    def __init__(self, request):
       self.request = request
    
    @property
    def session(self):
        return get_session(self.request)

    def isValid(self, token):
        session = self.session
        existing = session\
            .query(TokenRecord)\
            .filter(TokenRecord.uid == token)\
            .first()
        if not existing:
            raise TokenNotExists()
        if existing.usage_count == 0:
            raise TokenUsageCountExceeded()
        current_time = datetime.now()
        if existing.last_used + timedelta(0, existing.lock_time) > current_time:
            raise TokenLockTimeViolation()
        if current_time > existing.valid_to or current_time < existing.valid_from:
            raise TokenTimeRangeViolation()
        if not existing.usage_count == -1:
            existing.usage_count =-1
        existing.last_used = current_time
        # alter table
        return True
        


class TokenException(Exception):
    ...


class TokenNotExists(TokenException):
    
    def __init__(self, token):
        self.token = token
        self.message = f"The token {self.token} doesn't exists"
        super().__init__(self.message)


class TokenUsageCountExceeded(TokenException):
        
    def __init__(self, token):
        self.token = token
        self.message = f"The token {self.token} has exceeded its durability"
        super().__init__(self.message)


class TokenLockTimeViolation(TokenException):
        
    def __init__(self, token):
        self.token = token
        self.message = f"The token {self.token} has been recently used and is on cooldown"
        super().__init__(self.message)


class TokenTimeRangeViolation(TokenException):
        
    def __init__(self, token):
        self.token = token
        self.message = f"The token {self.token} isn't in his valid Date Range"
        super().__init__(self.message)
