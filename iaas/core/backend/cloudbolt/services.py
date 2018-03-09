import json

from iaas.core.backend.cloudbolt.collection import IaaSCloudboltCollection
from iaas.core.backend.cloudbolt.object import IaaSCloudboltObject


class Services(IaaSCloudboltCollection):

    def __init__(self, config):
        super(Services, self).__init__(config, Service)


class Service(IaaSCloudboltObject):

    def __init__(self, config, *args, **kw):
        super(Service, self).__init__(config, *args, **kw)
