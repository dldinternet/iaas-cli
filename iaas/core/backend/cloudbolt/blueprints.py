import json

from iaas.core.backend.cloudbolt.client import Client
from iaas.core.backend.cloudbolt.collection import IaaSCloudboltCollection
from iaas.core.backend.cloudbolt.object import IaaSCloudboltObject
from iaas.core.exc import IaaSError


class Blueprints(IaaSCloudboltCollection):

    def __init__(self, config):
        super(Blueprints, self).__init__(config, Blueprint)


class Blueprint(IaaSCloudboltObject):

    def __init__(self, config, *args, **kw):
        super(Blueprint, self).__init__(config, *args, **kw)
