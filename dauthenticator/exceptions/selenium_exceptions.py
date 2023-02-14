class SeleniumException(Exception):
    def __init__(self, message=None):
        self.message = message


class SeleniumStatusException(SeleniumException):
    def __str__(self):
        if self.message:
            return f"SeleniumStatusException : {self.message} "
        else:
            return "SeleniumStatusException has been raised"
