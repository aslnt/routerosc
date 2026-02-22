class Error(Exception):
    pass


class ServiceError(Error):
    def __init__(self, reason):
        self.reason = reason

    def __str__(self):
        return f"Service error: {self.reason}"


class CommandError(Error):
    def __init__(self, execution):
        self.execution = execution

    def __str__(self):
        return f"Command error: {self.execution.errors}"
