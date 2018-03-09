"""IaaS base controller."""
import os

from iaas.cli.controllers.abstract import IaaSAbstractController
from iaas.core import VERSION, OWNER

BANNER = """
IaaS CLI v%s
Copyright (c) 2018 %s
""" % (VERSION, OWNER)


class IaaSBaseController(IaaSAbstractController):
    class Meta:
        label = 'base'
        description = 'IaaS'
        arguments = [
            (['-v', '--version'], dict(action='version', version=BANNER)),
        ]
        min_args = 2
