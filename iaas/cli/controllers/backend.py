"""IaaS backend base controller."""
from ConfigParser import NoSectionError

from iaas.cli.controllers.abstract import IaaSAbstractController


class IaaSBackendAbstractController(IaaSAbstractController):
    class Meta:
        label = 'backend'
        description = 'IaaS backend'
        min_args = 2
