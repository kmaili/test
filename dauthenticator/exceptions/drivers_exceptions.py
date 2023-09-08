class DriversException(Exception):
    def __init__(self, message=None):
        self.message = message


class AccountLoginException(DriversException):
    def __str__(self):
        if self.message:
            return f"AccountLoginException: {self.message} "
        else:
            return "AccountLoginException has been raised"

