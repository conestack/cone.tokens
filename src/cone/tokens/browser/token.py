from cone.app.browser.authoring import ContentAddForm
from cone.app.browser.authoring import ContentEditForm
from cone.app.browser.contents import ContentsTile
from cone.app.browser.form import Form
from cone.app.browser.layout import ProtectedContentTile
from cone.app.browser.utils import make_url
from cone.app.utils import add_creation_metadata
from cone.app.utils import update_creation_metadata
from cone.tile import tile
from cone.tokens.model import TokenContainer
from cone.tokens.model import TokenNode
from node.utils import UNSET
from plumber import plumbing
from pyramid.i18n import TranslationStringFactory
from yafowil.base import factory
from yafowil.persistence import node_attribute_writer
import uuid

_ = TranslationStringFactory('cone.tokens')


@tile(
    name='content',
    path='templates/token.pt',
    interface=TokenNode,
    permission='view')
class TokenTile(ProtectedContentTile):
    ...


class TokenForm(Form):
    form_name = 'tokenform'

    @property
    def form_action(self):
        return make_url(
            self.request,
            node=self.model,
            resource=self.action_resource
        )

    def prepare(self):
        form = self.form = factory(
            '#form',
            name=self.form_name,
            props={
                'action': self.form_action,
                'persist_writer': node_attribute_writer
            }
        )
        attrs = self.model.attrs
        form['valid_from'] = factory(
            '#field:label:error:datetime',
            value=attrs.get('valid_from', UNSET),
            props={
                'label': 'Valid from',
                'datepicker': True,
                'locale': 'de',
                'persist': True
            }
        )
        form['valid_to'] = factory(
            '#field:label:error:datetime',
            value=attrs.get('valid_to', UNSET),
            props={
                'label': 'Valid to',
                'datepicker': True,
                'locale': 'de',
                'persist': True,
                'required': 'Valid to field cannot be empty'
            }
        )
        form['usage_count'] = factory(
            '#field:label:error:number',
            value=attrs.get('usage_count', UNSET),
            props={
                'label': 'Usage Count',
                'required': 'Usage Count field cannot be empty'
            }
        )
        form['lock_time'] = factory(
            '#field:label:error:number',
            value=attrs.get('lock_time', UNSET),
            props={
                'label': 'Lock Time',
                'required': 'Lock time field cannot be empty'
            }
        )
        form['save'] = factory(
            'submit',
            props={
                'action': 'save',
                'expression': True,
                'handler': self.save,
                'next': self.next,
                'label': 'Save'
            }
        )
        form['cancel'] = factory(
            'submit',
            props={
                'action': 'cancel',
                'expression': True,
                'skip': True,
                'next': self.next,
                'label': 'Cancel'
            }
        )

    def save(self, widget, data):
        data.write(self.model)


@tile(name='addform', interface=TokenNode, permission='add')
@plumbing(ContentAddForm)
class TokenAddForm(TokenForm):

    def save(self, widget, data):
        super(TokenAddForm, self).save(widget, data) 
        self.model.parent[str(uuid.uuid4())] = self.model
        add_creation_metadata(self.request, self.model.attrs)
        self.model()


@tile(name='editform', interface=TokenNode, permission='edit')
@plumbing(ContentEditForm)
class TokenEditForm(TokenForm):

    def save(self, widget, data):
        super(TokenEditForm, self).save(widget, data)
        update_creation_metadata(self.request, self.model.attrs)
        self.model()

@tile(
    name='contents',
    path='templates/tokens.pt',
    interface=TokenNode,
    permission='view')
class TokenCotainerTile(ContentsTile):
    #XXX: needs testing
    ...