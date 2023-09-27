from cone.app import get_root
from cone.sql import testing as sql_testing
from cone.tokens.model import TokenContainer
from cone.tokens.model import TokenNode
from cone.tokens.model import TokenRecord
from cone.tokens.tests import tokens_layer
from datetime import datetime
from node.tests import NodeTestCase
import uuid


class TestModel(NodeTestCase):
    layer = tokens_layer

    @sql_testing.delete_table_records(TokenRecord)
    def test_TokenContainer(self):
        tokens = get_root()['tokens']

        self.assertEqual(tokens.record_class, TokenRecord)
        self.assertEqual(tokens.child_factory, TokenNode)
        self.assertEqual(
            tokens.uuid,
            uuid.UUID('c40ef458-832f-42e6-9add-2dda2afb8920')
        )

        self.assertEqual(tokens.metadata.title, 'token_container_title')
        self.assertEqual(
            tokens.metadata.description,
            'token_container_description'
        )

        self.assertTrue(tokens.properties.in_navtree)
        self.assertTrue(tokens.properties.action_up)
        #self.assertTrue(tokens.properties.action_sharing)
        self.assertTrue(tokens.properties.action_view)
        self.assertTrue(tokens.properties.action_list)

    @sql_testing.delete_table_records(TokenRecord)
    def test_TokenNode(self):
        tokens = get_root()['tokens']
        self.assertEqual(isinstance(tokens, TokenContainer), True)

        # add token to tokens container
        token = TokenNode()
        token.attrs['value'] = 'value'
        token.attrs['valid_from'] = datetime(2023, 9, 21)
        token.attrs['valid_to'] = datetime(2023, 9, 22)
        token.attrs['lock_time'] = 0
        token.attrs['usage_count'] = -1
        token.attrs['creator'] = 'admin'
        token.attrs['created'] = datetime(2023, 9, 21)
        token.attrs['modified'] = datetime(2023, 9, 21)

        tokens[str(token.uuid)] = token
        token()

        # check if token has been added
        self.assertEqual(len(tokens), 1)
        token = tokens.values()[0]
        self.assertTrue(isinstance(token, TokenNode))
        self.assertEqual(token.attrs['value'], 'value')
        self.assertEqual(token.attrs['valid_from'], datetime(2023, 9, 21))
        self.assertEqual(token.attrs['valid_to'], datetime(2023, 9, 22))
        self.assertEqual(token.attrs['lock_time'], 0)
        self.assertEqual(token.attrs['usage_count'], -1)
        self.assertEqual(token.attrs['creator'], 'admin')
        self.assertEqual(token.attrs['created'], datetime(2023, 9, 21))
        self.assertEqual(token.attrs['modified'], datetime(2023, 9, 21))

        # check metadata
        self.assertEqual(token.metadata.title, 'value')
        self.assertEqual(token.metadata.creator, 'admin')
        self.assertEqual(token.metadata.created, datetime(2023, 9, 21))
        self.assertEqual(token.metadata.modified, datetime(2023, 9, 21))

        # check properties
        self.assertTrue(token.properties.action_up)
        self.assertEqual(token.properties.action_up_tile, 'content')
        self.assertTrue(token.properties.action_edit)
        self.assertTrue(token.properties.action_view)
