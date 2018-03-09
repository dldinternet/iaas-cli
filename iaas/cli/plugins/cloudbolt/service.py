"""CloudboltPlugin for IaaS."""
from cement.ext.ext_argparse import expose
from iaas.core.backend.cloudbolt.services import Services, Service
from ..cloudbolt import CloudboltPluginController


class CloudboltPluginServiceController(CloudboltPluginController):
    class Meta:
        # name that the controller is displayed at command line
        label = 'service'

        # text displayed next to the label in ``--help`` output
        description = 'The CloudBolt service plugin for IaaS'

        # stack this controller on-top of ``base`` (or any other controller)
        stacked_on = 'cloudbolt'

        # determines whether the controller is nested, or embedded
        stacked_type = 'nested'

        min_args = 3
        arguments = [
            (
                ['-S', '--service'],
                dict(
                    help='Show service with this reference (id or href)',
                    action='store',
                )
            ),
            (
                ['--all'],
                dict(
                    help='Show all services',
                    action='store_true',
                )
            ),
            (
                ['--quick'],
                dict(
                    help='Show only basic service info',
                    action='store_true',
                )
            ),
            (
                ['--batch'],
                dict(
                    help='Batch mode. Do not wait around for order to complete',
                    action='store_true',
                )
            ),
        ]

    @expose(help="CloudBolt Services list IaaS sub-command.")
    def list(self):
        if self.app._parsed_args.filters is None and not self.app._parsed_args.all and not self.app._parsed_args.quick:
            self.app._parsed_args.filters = 'status:Active'
            self.app.log.info('Setting filters to {}'.format(self.app._parsed_args.filters))
        if not self.app._parsed_args.quick:
            self.app._parsed_args.detailed=True
            self.app.log.info('Not a --quick list. Asking for service details')
        self.app.log.info('Not a --quick list. Asking for service details')
        self.render(self._list(Services(self.app.config.get_section_dict('cloudbolt')), parameters=self.app._parsed_args.__dict__))

    @expose(help="CloudBolt IaaS delete service.")
    def delete(self):
        recipe = [
            {'parameter': 'service', 'description': 'The target service',    'ask': True, 'hint': 'An Id or href for a service. Refer to "service list".', 'options': {
                'module': 'iaas.core.backend.cloudbolt.services',
                'class': 'Services',
                'method': 'list',
                'attribute': { 'show': ['name','status'], 'use': '_links/self/href', 'filters': [['status','Active']], 'alternatives': ['_links/self/title', '_links/self/href'] },
                'section': 'cloudbolt',
            } },
        ]
        self.app.log.info('Check the recipe')
        self.check_recipe(recipe=recipe)

        self.app.log.info('Start the service delete order')
        order = self._start_order(type='delete', resource='service')
        self.app.log.info('Add the decom-items to the order')
        order.delete(pargs=self.app._parsed_args.__dict__, resource='service')
        self.app.log.info('Submit the order: {}'.format(order))
        self._submit_order(order)


def load(app):
    # register the plugin class.. this only happens if the plugin is enabled
    app.handler.register(CloudboltPluginServiceController)
