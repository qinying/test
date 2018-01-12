__author__ = 'jesse'

class KancheException(Exception):

    def __init__(self, msg):
        Exception.__init__(self)
        self.msg = msg


class HttpGetParamTypeException(KancheException):

    def __init__(self, msg):
        KancheException.__init__(self. msg)
        self.msg = msg
