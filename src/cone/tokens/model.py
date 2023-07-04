from cone.app.model import Metadata
from cone.sql import SQLBase
from cone.sql.model import GUID
from cone.sql.model import SQLRowNode
from cone.sql.model import SQLTableNode
from node.utils import instance_property
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String

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
        md.last_used = self.attrs.get('last_used')
        md.valid_from = self.attrs.get('valid_from')
        md.valid_to = self.attrs.get('valid_to')
        md.usage_count = self.attrs.get('usage_count')
        md.lock_time = self.attrs.get('lock_time')
        md.creator = self.attrs.get('creator')
        md.created = self.attrs.get('created')
        md.modified = self.attrs.get('modified')
        return md


class TokenContainer(SQLTableNode):
    record_class = TokenRecord
    child_factory = TokenNode