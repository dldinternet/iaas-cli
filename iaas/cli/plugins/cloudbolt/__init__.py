from ..cloudbolt.controller import CloudboltPluginController
from ..cloudbolt.blueprint import CloudboltPluginBlueprintController
from ..cloudbolt.order import CloudboltPluginOrderController
from ..cloudbolt.job import CloudboltPluginJobController
from ..cloudbolt.server import CloudboltPluginServerController
from ..cloudbolt.user import CloudboltPluginUserController
from ..cloudbolt.group import CloudboltPluginGroupController
from ..cloudbolt.environment import CloudboltPluginEnvironmentController
from ..cloudbolt.service import CloudboltPluginServiceController

def load(app):
    app.handler.register(CloudboltPluginController)
    app.handler.register(CloudboltPluginBlueprintController)
    app.handler.register(CloudboltPluginOrderController)
    app.handler.register(CloudboltPluginJobController)
    app.handler.register(CloudboltPluginServerController)
    app.handler.register(CloudboltPluginUserController)
    app.handler.register(CloudboltPluginGroupController)
    app.handler.register(CloudboltPluginEnvironmentController)
    app.handler.register(CloudboltPluginServiceController)
