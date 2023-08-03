class TokenException(Exception):

    def as_json(self):
        return dict(success=False, message=self.message)

class TokenNotExists(TokenException):

    def __init__(self, token_uid):
        self.token_uid = token_uid
        self.message = f'The token {self.token_uid} doesn\'t exists'
        super().__init__(self.message)


class TokenUsageCountExceeded(TokenException):

    def __init__(self, token_uid):
        self.token_uid = token_uid
        self.message = f'The token {self.token_uid} has exceeded its durability'
        super().__init__(self.message)


class TokenLockTimeViolation(TokenException):

    def __init__(self, token_uid):
        self.token_uid = token_uid
        self.message = f'The token {self.token_uid} has been recently used and is on cooldown'
        super().__init__(self.message)


class TokenTimeRangeViolation(TokenException):

    def __init__(self, token_uid):
        self.token_uid = token_uid
        self.message = f'The token {self.token_uid} isn\'t in his valid Date Range'
        super().__init__(self.message)


class TokenValueError(TokenException):

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)