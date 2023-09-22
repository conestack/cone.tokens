from cone.sql import get_session
from cone.sql import testing as sql_testing
from cone.tokens.api import TokenAPI
from cone.tokens.exceptions import TokenLockTimeViolation
from cone.tokens.exceptions import TokenNotExists
from cone.tokens.exceptions import TokenTimeRangeViolation
from cone.tokens.exceptions import TokenUsageCountExceeded
from cone.tokens.exceptions import TokenValueError
from cone.tokens.model import TokenRecord
from cone.tokens.tests import tokens_layer
from datetime import datetime 
from datetime import timedelta
from node.tests import NodeTestCase
import uuid


class TestTokenAPI(NodeTestCase):
    layer = tokens_layer

    @sql_testing.delete_table_records(TokenRecord)
    def test__get_token(self):
        request = self.layer.new_request()
        session = get_session(request)

        token = TokenRecord()
        token_uid = token.uid = uuid.uuid4()

        session.add(token)
        session.commit()

        api = TokenAPI(request)
        self.assertEqual(api._get_token(token_uid).uid, token_uid)

        invalid_uid = uuid.UUID('f9c98a6b-b773-4714-b965-98c7911e6236')
        with self.assertRaises(TokenNotExists) as arc:
            api._get_token(invalid_uid)
        self.assertEqual(
            str(arc.exception),
            'Token f9c98a6b-b773-4714-b965-98c7911e6236 not exists'
        )

    @sql_testing.delete_table_records(TokenRecord)
    def test__query_token(self):
        request = self.layer.new_request()
        session = get_session(request)

        token = TokenRecord()
        token_uid = token.uid = uuid.uuid4()
        token_value = token.value = 'token value'

        session.add(token)
        session.commit()

        api = TokenAPI(request)
        self.assertEqual(api._query_token(''), None)
        self.assertEqual(api._query_token(token_value).uid, token_uid)

    @sql_testing.delete_table_records(TokenRecord)
    def test_consume(self):
        request = self.layer.new_request()
        session = get_session(request)

        token = TokenRecord()
        token_uid = uuid.UUID('577989d4-1673-4639-a579-dd468b294713')
        token.uid = token_uid
        token.value = 'token value'
        last_used = token.last_used = datetime(2023, 1, 1)
        token.valid_from = None
        token.valid_to = None
        token.lock_time = 0
        token.usage_count = -1
        session.add(token)

        api = TokenAPI(request)
        self.assertTrue(api.consume(token_uid))
        self.assertNotEqual(last_used, token.last_used)
        self.assertEqual(token.usage_count, -1)

        token.usage_count = 1
        session.commit()
        self.assertTrue(api.consume(token_uid))
        self.assertEqual(token.usage_count, 0)

        with self.assertRaises(TokenUsageCountExceeded) as arc:
            api.consume(token_uid)
        self.assertEqual(
            str(arc.exception),
            'Token 577989d4-1673-4639-a579-dd468b294713 usage count exceeded'
        )

        token.usage_count = -1
        token.lock_time = 120
        session.commit()
        with self.assertRaises(TokenLockTimeViolation) as arc:
            api.consume(token_uid)
        self.assertEqual(
            str(arc.exception),
            'Token 577989d4-1673-4639-a579-dd468b294713 is locked'
        )

        token.lock_time = 0
        session.commit()
        self.assertTrue(api.consume(token_uid))

        token.valid_from = datetime.now() + timedelta(days=1)
        session.commit()
        with self.assertRaises(TokenTimeRangeViolation) as arc:
            api.consume(token_uid)
        self.assertEqual(
            str(arc.exception),
            'Token 577989d4-1673-4639-a579-dd468b294713 out of time range'
        )

        token.valid_from = None
        token.valid_to = datetime.now() - timedelta(days=1)
        session.commit()
        with self.assertRaises(TokenTimeRangeViolation) as arc:
            api.consume(token_uid)
        self.assertEqual(
            str(arc.exception),
            'Token 577989d4-1673-4639-a579-dd468b294713 out of time range'
        )

        token.valid_from = datetime.now() - timedelta(days=1)
        token.valid_to = datetime.now() + timedelta(days=1)
        session.commit()

        self.assertTrue(api.consume(token_uid))

        session.delete(token)
        with self.assertRaises(TokenNotExists) as arc:
            api.consume(token_uid)
        self.assertEqual(
            str(arc.exception),
            'Token 577989d4-1673-4639-a579-dd468b294713 not exists'
        )

    @sql_testing.delete_table_records(TokenRecord)
    def test_add(self):
        request = self.layer.new_request()
        api = TokenAPI(request)
        token_uid = uuid.UUID('c27b6d86-8ac0-4261-9e62-151ff7e31ecb')
        api.add(token_uid)

        token = api._get_token(token_uid)
        self.assertEqual(token.value, str(token_uid))
        self.assertEqual(token.valid_from, None)
        self.assertEqual(token.valid_to, None)
        self.assertEqual(token.usage_count, -1)
        self.assertEqual(token.lock_time, 0)

        token_uid = uuid.UUID('6556f43e-b0ce-4c14-a0c5-40b8f2cdab3a')
        api.add(
            token_uid,
            value='token value',
            valid_from=datetime(2023, 9, 21),
            valid_to=datetime(2023, 9, 22),
            usage_count=0,
            lock_time=10
        )
        token = api._get_token(token_uid)
        self.assertEqual(token.value, 'token value')
        self.assertEqual(token.valid_from, datetime(2023, 9, 21))
        self.assertEqual(token.valid_to, datetime(2023, 9, 22))
        self.assertEqual(token.usage_count, 0)
        self.assertEqual(token.lock_time, 10)

        with self.assertRaises(TokenValueError) as arc:
            api.add(
                token_uid,
                valid_from=datetime(2023, 9, 21),
                valid_to=datetime(2023, 9, 21),
            )
        self.assertEqual(
            str(arc.exception),
            'Token with uid 6556f43e-b0ce-4c14-a0c5-40b8f2cdab3a already exists'
        )

        token_uid = uuid.UUID('9c9196f0-8b5b-42e7-b389-b13b267c9378')
        with self.assertRaises(TokenValueError) as arc:
            api.add(
                token_uid,
                valid_from=datetime(2023, 9, 21),
                valid_to=datetime(2023, 9, 21),
            )
        self.assertEqual(
            str(arc.exception),
            'valid_from must be before valid_to'
        )

    @sql_testing.delete_table_records(TokenRecord)
    def test_delete(self):
        request = self.layer.new_request()
        session = get_session(request)

        token = TokenRecord()
        token_uid = token.uid = uuid.UUID('cc3ebacb-1fc1-42ea-bc24-051b60d60545')
        session.add(token)
        session.commit()

        api = TokenAPI(request)
        api.delete(token_uid)
        with self.assertRaises(TokenNotExists) as arc:
            api.delete(token_uid)
        self.assertEqual(
            str(arc.exception),
            'Token cc3ebacb-1fc1-42ea-bc24-051b60d60545 not exists'
        )

    @sql_testing.delete_table_records(TokenRecord)
    def test_update(self):
        request = self.layer.new_request()
        session = get_session(request)

        token = TokenRecord()
        token_uid = token.uid = uuid.UUID('17b04001-4f42-4061-ad85-72de9ed8e287')
        token.value = 'value'
        session.add(token)

        token = TokenRecord()
        token.uid = uuid.UUID('c32e818c-af0c-4ee4-a855-0e50cad09e13')
        token.value = 'other value'
        session.add(token)
        session.commit()

        api = TokenAPI(request)
        with self.assertRaises(TokenValueError) as arc:
            api.update(token_uid, value='other value')
        self.assertEqual(
            str(arc.exception),
            'Given value already used by another token'
        )

        with self.assertRaises(TokenValueError) as arc:
            api.update(
                token_uid,
                valid_from=datetime(2023, 9, 21),
                valid_to=datetime(2023, 9, 21)
            )
        self.assertEqual(
            str(arc.exception),
            'valid_from must be before valid_to'
        )

        api.update(
            token_uid,
            value='new value',
            valid_from=datetime(2023, 9, 21),
            valid_to=datetime(2023, 9, 22),
            usage_count=10,
            lock_time=100
        )
        token = session\
            .query(TokenRecord)\
            .filter(TokenRecord.uid == token_uid)\
            .one()

        self.assertEqual(token.value, 'new value')
        self.assertEqual(token.valid_from, datetime(2023, 9, 21))
        self.assertEqual(token.valid_to, datetime(2023, 9, 22))
        self.assertEqual(token.usage_count, 10)
        self.assertEqual(token.lock_time, 100)
