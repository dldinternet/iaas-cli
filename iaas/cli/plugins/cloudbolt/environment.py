"""CloudboltPlugin for IaaS."""
from cement.ext.ext_argparse import expose
from iaas.core.backend.cloudbolt.environments import Environments
from ..cloudbolt import CloudboltPluginController


class CloudboltPluginEnvironmentController(CloudboltPluginController):
    class Meta:
        # name that the controller is displayed at command line
        label = 'environment'

        # text displayed next to the label in ``--help`` output
        description = 'The CloudBolt environment plugin for IaaS'

        # stack this controller on-top of ``base`` (or any other controller)
        stacked_on = 'cloudbolt'

        # determines whether the controller is nested, or embedded
        stacked_type = 'nested'

        # [2018-02-20 Christo] This seems to be too late ... for certain hooks?
        # hooks = [
        #     ('pre_argument_parsing', hook_pre_argument_parsing),
        #     ('post_argument_parsing', hook_post_argument_parsing),
        # ]
        min_args = 3
        arguments = [
            (
                ['-e', '--environment'],
                dict(
                    help='Environment',
                    action='store',
                )
            ),
        ]

        # headers = {'_links': 'LINKS', 'id': 'ID', 'name': 'NAME'}
        # table_format = 'grid'

    @expose(help="CloudBolt Environments list IaaS sub-command.")
    def list(self):
        self.render(self._list(Environments(self.app.config.get_section_dict('cloudbolt')), parameters=self.app._parsed_args.__dict__))


def load(app):
    # register the plugin class.. this only happens if the plugin is enabled
    app.handler.register(CloudboltPluginEnvironmentController)

    # register a hook (function) to run after arguments are parsed.
    # [2018-02-20 Christo] Use the plugin _pre/_post method overrides
    # app.hook.register('post_argument_parsing', hook_post_argument_parsing)
    # app.hook.register('pre_argument_parsing', hook_pre_argument_parsing)
