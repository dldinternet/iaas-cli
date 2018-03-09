import json

from iaas.core.backend.cloudbolt.client import Client
from iaas.core.backend.cloudbolt.collection import IaaSCloudboltCollection
from iaas.core.backend.cloudbolt.object import IaaSCloudboltObject
from iaas.core.exc import IaaSError


class Jobs(IaaSCloudboltCollection):

    def __init__(self, config):
        super(Jobs, self).__init__(config, Job)


class Job(IaaSCloudboltObject):

    def __init__(self, config, *args, **kw):
        super(Job, self).__init__(config, *args, **kw)
