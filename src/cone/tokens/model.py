from cone.app.model import Metadata, Properties
from cone.app.model import node_info
from cone.sql import SQLBase
from cone.sql.acl import SQLPrincipalACL
from cone.sql.model import GUID
from cone.sql.model import SQLRowNode
from cone.sql.model import SQLTableNode
from node.utils import instance_property
from plumber import plumbing
from pyramid.i18n import TranslationStringFactory
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String


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
        props.default_content_tile = 'sharing'
        props.in_navtree = True
        props.action_up = True
        return props

    @property
    def metadata(self):
        md = Metadata()
        info = self.nodeinfo
        md.title = info.title
        md.description = info.description
        return md