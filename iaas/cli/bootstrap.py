"""IaaS bootstrapping."""

# All built-in application controllers should be imported, and registered
# in this file in the same way as IaaSBaseController.

from iaas.cli.controllers.base import IaaSBaseController

def load(app):
    app.handler.register(IaaSBaseController)
