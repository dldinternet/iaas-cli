"""CloudboltPlugin for IaaS."""
from cement.ext.ext_argparse import expose
from iaas.core.backend.cloudbolt.blueprints import Blueprints
from ..cloudbolt import CloudboltPluginController


class CloudboltPluginBlueprintController(CloudboltPluginController):
    class Meta:
        # name that the controller is displayed at command line
        label = 'blueprint'

        # text displayed next to the label in ``--help`` output
        description = 'The CloudBolt blueprint plugin for IaaS'

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
            (
                ['-s', '--server'],
                dict(
                    help='Server',
                    action='store',
                )
            ),
            (
                ['-G', '--group'],
                dict(
                    help='Group href or id',
                    action='store',
                )
            ),
            (
                ['-B', '--blueprint'],
                dict(
                    help='Blueprint href or id',
                    action='store',
                )
            ),
        ]

        # headers = {'_links': 'LINKS', 'id': 'ID', 'name': 'NAME'}
        # table_format = 'grid'

    @expose(help="CloudBolt Blueprints list IaaS sub-command.")
    def list(self):
        self.render(self._list(Blueprints(self.app.config.get_section_dict('cloudbolt')), parameters=self.app._parsed_args.__dict__))


def load(app):
    # register the plugin class.. this only happens if the plugin is enabled
    app.handler.register(CloudboltPluginBlueprintController)

    # register a hook (function) to run after arguments are parsed.
    # [2018-02-20 Christo] Use the plugin _pre/_post method overrides
    # app.hook.register('post_argument_parsing', hook_post_argument_parsing)
    # app.hook.register('pre_argument_parsing', hook_pre_argument_parsing)
