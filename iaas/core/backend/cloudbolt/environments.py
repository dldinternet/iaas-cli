import json

from iaas.core.backend.cloudbolt.client import Client
from iaas.core.backend.cloudbolt.collection import IaaSCloudboltCollection
from iaas.core.backend.cloudbolt.errors import IaaSCloudboltAPIError
from iaas.core.backend.cloudbolt.object import IaaSCloudboltObject
from iaas.core.exc import IaaSError


class Environments(IaaSCloudboltCollection):

    def __init__(self, config):
        super(Environments, self).__init__(config, Environment)

    def find(self, *args, **kw):
        kw['ref'] = kw.get('ref', kw.get('environment', None))
        try:
            env = Environment(self.config, None, ref=kw.get('ref', None))
            if not env.href():
                return None
        except IaaSCloudboltAPIError as e:
            env = Environment(self.config, None)
            env.href(ref=kw.get('ref', None))
        return env



class Environment(IaaSCloudboltObject):

    def __init__(self, config, *args, **kw):
        super(Environment, self).__init__(config, *args, **kw)
