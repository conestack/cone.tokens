from cone.app.interfaces import INavigationLeaf
from cone.app.model import Metadata
from cone.app.model import Properties
from cone.app.model import UUIDAttributeAware
from cone.app.model import node_info
from cone.sql import SQLBase
#from cone.sql.acl import SQLPrincipalACL
from cone.sql.model import GUID
from cone.sql.model import SQLRowNode
from cone.sql.model import SQLTableNode
from node.interfaces import IUUID
from node.utils import instance_property
from plumber import plumbing
from pyramid.i18n import TranslationStringFactory
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from zope.interface import implementer
import uuid


_ = TranslationStringFactory('cone.tokens')


class TokenRecord(SQLBase):
    __tablename__ = 'tokens'

    uid = Column(GUID, primary_key=True)
    value = Column(String)
    last_used = Column(DateTime)
    valid_from = Column(DateTime)
    valid_to = Column(DateTime)
    usage_count = Column(Integer)
    lock_time = Column(Integer)  # in seconds
    creator = Column(String)
    created = Column(DateTime)
    modified = Column(DateTime)


@node_info(
    name='token_node',
    title=_('token_node_title', default='Token'),
    description=_('token_node_description', default='Token'))
@plumbing(UUIDAttributeAware)
@implementer(INavigationLeaf)
class TokenNode(SQLRowNode):
    record_class = TokenRecord
    uuid_attribute_name = 'uid'

    @property
    def properties(self):
        props = Properties()
        props.action_up = True
        props.action_up_tile = 'content'
        props.action_edit = True
        props.action_view = True
        props.action_delete = True
        return props

    @instance_property
    def metadata(self):
        md = Metadata()
        md.title = str(self.attrs.get('value'))
        md.creator = self.attrs.get('creator')
        md.created = self.attrs.get('created')
        md.modified = self.attrs.get('modified')
        return md


@node_info(
    name='token_container',
    title=_('token_container_title', default='Tokens'),
    description=_('token_container_description', default='Tokens'),
    addables=['token_node'])
#@plumbing(SQLPrincipalACL)
@implementer(IUUID)
class TokenContainer(SQLTableNode):
    record_class = TokenRecord
    child_factory = TokenNode
    uuid = uuid.UUID('c40ef458-832f-42e6-9add-2dda2afb8920')

    @property
    def properties(self):
        props = Properties()
        props.in_navtree = True
        props.action_up = True
        #props.action_sharing = True
        props.action_view = True
        props.action_list = True
        return props

    @property
    def metadata(self):
        md = Metadata()
        info = self.nodeinfo
        md.title = info.title
        md.description = info.description
        return md


class TokenUsageRecord(SQLBase):
    __tablename__ = 'token_usage'

    uid = Column(GUID, primary_key=True)
    token_uid = Column(GUID)
    token_value = Column(String)
    timestamp = Column(DateTime)
    error_code = Column(Integer)
    user = Column(String)
