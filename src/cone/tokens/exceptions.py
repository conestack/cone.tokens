class TokenException(Exception):

    def as_json(self):
        return dict(success=False, message=self.message)


class TokenNotExists(TokenException):

    def __init__(self, token_uid):
        self.token_uid = token_uid
        self.message = f'Token {self.token_uid} not exists'
        super().__init__(self.message)


class TokenUsageCountExceeded(TokenException):

    def __init__(self, token_uid):
        self.token_uid = token_uid
        self.message = f'Token {self.token_uid} usage count exceeded'
        super().__init__(self.message)


class TokenLockTimeViolation(TokenException):

    def __init__(self, token_uid):
        self.token_uid = token_uid
        self.message = f'Token {self.token_uid} is locked'
        super().__init__(self.message)


class TokenTimeRangeViolation(TokenException):

    def __init__(self, token_uid):
        self.token_uid = token_uid
        self.message = f'Token {self.token_uid} out of time range'
        super().__init__(self.message)


class TokenValueError(TokenException):

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class TokenAPIError(TokenException):

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
