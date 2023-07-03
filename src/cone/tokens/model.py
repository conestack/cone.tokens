from cone.sql import SQLBase
from cone.sql.model import GUID
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import INTEGER


class TokenRecord(SQLBase):
    __tablename__ = 'tokens'

    uid = Column(GUID, primary_key=True)
    last_used = Column(DateTime)
    valid_from = Column(DateTime)
    valid_to = Column(DateTime)
    usage_count = Column(INTEGER)
    lock_time = Column(INTEGER) # in seconds
