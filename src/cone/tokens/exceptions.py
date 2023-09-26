class TokenException(Exception):

    def __init__(self, message, error_code=0):
        self.message = message
        self.error_code = error_code
        super().__init__(message)

    def as_json(self):
        return dict(success=False, message=self.message)


class TokenNotExists(TokenException):

    def __init__(self, token_uid):
        self.token_uid = token_uid
        super().__init__(f'Token {self.token_uid} not exists', 1)


class TokenUsageCountExceeded(TokenException):

    def __init__(self, token_uid):
        self.token_uid = token_uid
        super().__init__(f'Token {self.token_uid} usage count exceeded', 2)


class TokenLockTimeViolation(TokenException):

    def __init__(self, token_uid):
        self.token_uid = token_uid
        super().__init__(f'Token {self.token_uid} is locked', 3)


class TokenTimeRangeViolation(TokenException):

    def __init__(self, token_uid):
        self.token_uid = token_uid
        super().__init__(f'Token {self.token_uid} out of time range', 4)


class TokenValueError(TokenException):

    def __init__(self, message, error_code=7):
        super().__init__(message, error_code)


class TokenAPIError(TokenException):

    def __init__(self, message, error_code=8):
        super().__init__(message, error_code)
