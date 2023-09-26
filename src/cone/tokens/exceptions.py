from node.utils import UNSET


class TokenException(Exception):
    error_code = UNSET

    def __init__(self, message):
        self.message = message
        super().__init__(message)

    def as_json(self):
        return dict(success=False, message=self.message)


class TokenNotExists(TokenException):
    error_code = 1

    def __init__(self, token_uid):
        self.token_uid = token_uid
        super().__init__(f'Token {self.token_uid} not exists')


class TokenUsageCountExceeded(TokenException):
    error_code = 2

    def __init__(self, token_uid):
        self.token_uid = token_uid
        super().__init__(f'Token {self.token_uid} usage count exceeded')


class TokenLockTimeViolation(TokenException):
    error_code = 3

    def __init__(self, token_uid):
        self.token_uid = token_uid
        super().__init__(f'Token {self.token_uid} is locked')


class TokenTimeRangeViolation(TokenException):
    error_code = 4

    def __init__(self, token_uid):
        self.token_uid = token_uid
        super().__init__(f'Token {self.token_uid} out of time range')


class TokenValueError(TokenException):
    error_code = 5

    def __init__(self, message):
        super().__init__(message)


class TokenAPIError(TokenException):
    error_code = 6

    def __init__(self, message):
        super().__init__(message)
