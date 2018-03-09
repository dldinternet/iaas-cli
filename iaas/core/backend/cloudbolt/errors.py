from iaas.core.exc import IaaSError


class IaaSCloudboltAPIError(IaaSError):
    def __init__(self, status, msg):
        super(IaaSError, self).__init__(self)
        self.status_code = status
        self.msg = msg

