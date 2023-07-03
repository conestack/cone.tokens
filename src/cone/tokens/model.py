from cone.sql import SQLBase
from cone.sql.model import GUID
from cone.app.model import Metadata
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import String
from sqlalchemy import Integer
from cone.sql.model import SQLRowNode
from cone.sql.model import SQLTableNode

class TokenRecord(SQLBase):
    __tablename__ = 'tokens'

    uid = Column(GUID, primary_key=True)
    last_used = Column(DateTime)
    valid_from = Column(DateTime)
    valid_to = Column(DateTime)
    usage_count = Column(Integer)
    lock_time = Column(Integer) # in seconds
    creator = Column(String)
    created = Column(DateTime)
    modified = Column(DateTime)


class TokenNode(SQLRowNode):
    record_class = TokenRecord

    @instance_property
    def metadata(self):
        md = Metadata()
        md.uid = self.attrs.get('uid')
        md.description = self.attrs.get('description')
        md.creator = self.attrs.get('creator')
        md.created = self.attrs.get('created')
        md.modified = self.attrs.get('modified')
        return md


class Tokens(SQLTableNode):
    record_class = TokenRecord
    child_factory = TokenNode