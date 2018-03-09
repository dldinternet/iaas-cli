"""IaaS exception classes."""

class IaaSError(StandardError):
    """Generic errors."""
    def __init__(self, msg):
        super(IaaSError, self).__init__(self)
        self.msg = msg

    def __str__(self):
        return self.msg

class IaaSConfigError(IaaSError):
    """Config related errors."""
    pass

class IaaSRuntimeError(IaaSError):
    """Generic runtime errors."""
    pass

class IaaSArgumentError(IaaSError):
    """Argument related errors."""
    pass
