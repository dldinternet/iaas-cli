"""CloudboltPlugin for IaaS."""
from cement.ext.ext_argparse import expose
from iaas.core.backend.cloudbolt.jobs import Jobs, Job
from ..cloudbolt import CloudboltPluginController


class CloudboltPluginJobController(CloudboltPluginController):
    class Meta:
        # name that the controller is displayed at command line
        label = 'job'

        # text displayed next to the label in ``--help`` output
        description = 'The CloudBolt job plugin for IaaS'

        # stack this controller on-top of ``base`` (or any other controller)
        stacked_on = 'cloudbolt'

        # determines whether the controller is nested, or embedded
        stacked_type = 'nested'

        min_args = 3
        arguments = [
            (
                ['-O', '--order'],
                dict(
                    help='Show order with this reference (id or href)',
                    action='store',
                )
            ),
        ]

    @expose(help="CloudBolt Jobs list IaaS sub-command.")
    def list(self):
        self.render(self._list(Jobs(self.app.config.get_section_dict('cloudbolt')), parameters=self.app._parsed_args.__dict__))


def load(app):
    # register the plugin class.. this only happens if the plugin is enabled
    app.handler.register(CloudboltPluginJobController)
