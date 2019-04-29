class BaseException(Exception):
    def __init__(self, error_code, error_msg=None):
        self.error_code = error_code
        self.error_msg = error_msg


class GetTokenError(BaseException):
    '''获取token 失败'''
    pass

class RedisServiceError(BaseException):
    """redis 连接错误"""
    pass