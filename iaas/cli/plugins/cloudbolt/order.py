"""CloudboltPlugin for IaaS."""
from cement.ext.ext_argparse import expose
from iaas.core.backend.cloudbolt.orders import Orders, Order
from iaas.core.exc import IaaSError
from ..cloudbolt import CloudboltPluginController


class CloudboltPluginOrderController(CloudboltPluginController):
    class Meta:
        # name that the controller is displayed at command line
        label = 'order'

        # text displayed next to the label in ``--help`` output
        description = 'The CloudBolt order plugin for IaaS'

        # stack this controller on-top of ``base`` (or any other controller)
        stacked_on = 'cloudbolt'

        # determines whether the controller is nested, or embedded
        stacked_type = 'nested'

        min_args = 3
        arguments = [
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
            (
                ['-O', '--order'],
                dict(
                    help='Show order with this reference (id or href)',
                    action='store',
                )
            ),
        ]


    @expose(help="CloudBolt Orders list IaaS sub-command.")
    def list(self):
        self.render(self._list(Orders(self.app.config.get_section_dict('cloudbolt')), parameters=self.app._parsed_args.__dict__))


    @expose(help="CloudBolt Orders show IaaS sub-command.")
    def show(self):
        if not self.app.pargs.order:
            raise IaaSError('Order ref is required')

        self._show(Orders(self.app.config.get_section_dict('cloudbolt')), ref=self.app.pargs.order)


    @expose(help="CloudBolt Orders show IaaS sub-command.")
    def cancel(self):
        # if not self.app.pargs.order:
        #     raise IaaSError('Order ref is required')

        orders = self._find(Orders(self.app.config.get_section_dict('cloudbolt')), ref=self.app.pargs.order)
        if len(orders) > 0:
            orders = [order.cancel() for order in orders]
        else:
            orders = [{"message": 'No orders found/matched'}]

        self.render(orders)


def load(app):
    # register the plugin class.. this only happens if the plugin is enabled
    app.handler.register(CloudboltPluginOrderController)
