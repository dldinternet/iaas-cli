from iaas.core.backend.cloudbolt.collection import IaaSCloudboltCollection
from iaas.core.backend.cloudbolt.errors import IaaSCloudboltAPIError
from iaas.core.backend.cloudbolt.object import IaaSCloudboltObject
from iaas.core.exc import IaaSError


class Servers(IaaSCloudboltCollection):

    def __init__(self, config):
        super(Servers, self).__init__(config, Server)


class Server(IaaSCloudboltObject):

    def __init__(self, config, *args, **kw):
        super(Server, self).__init__(config, *args, **kw)
