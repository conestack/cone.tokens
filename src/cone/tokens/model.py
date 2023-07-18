from cone.app.model import Metadata, Properties
from cone.app.model import node_info
from cone.sql import SQLBase
from cone.sql.acl import SQLPrincipalACL
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

_ = TranslationStringFactory('cone.tokens')


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


@node_info(
    name='token_node',
    title=_('token_node_title', default='Token'),
    description=_(
        'token_node_description',
        default='Token'
    ))
class TokenNode(SQLRowNode):
    record_class = TokenRecord

    @instance_property
    def metadata(self):
        md = Metadata()
        md.title = str(self.attrs.get('uid'))
        md.creator = self.attrs.get('creator')
        md.created = self.attrs.get('created')
        md.modified = self.attrs.get('modified')
        return md
    
@implementer(IUUID)
@node_info(
    name='token_container',
    title=_('token_container_title', default='Tokens'),
    description=_('token_container_description', default='Tokens'),
    addables=['token_node'])
@plumbing(SQLPrincipalACL)
class TokenContainer(SQLTableNode):
    record_class = TokenRecord
    child_factory = TokenNode

    @property
    def properties(self):
        props = Properties()
        props.default_content_tile = 'listing'
        props.in_navtree = True
        props.action_up = True
        props.action_sharing = True
        return props

    @property
    def metadata(self):
        md = Metadata()
        info = self.nodeinfo
        md.title = info.title
        md.description = info.description
        return md