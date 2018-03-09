"""CloudboltPlugin for IaaS."""
import string

import datetime
from collections import OrderedDict
from time import sleep

from cement.ext.ext_argparse import expose
from iaas.core.backend.cloudbolt.blueprints import Blueprint
from iaas.core.backend.cloudbolt.jobs import Job
from iaas.core.backend.cloudbolt.orders import Order
from iaas.core.backend.cloudbolt.servers import Servers, Server
from iaas.core.exc import IaaSError
from ..cloudbolt import CloudboltPluginController


class CloudboltPluginServerController(CloudboltPluginController):
    class Meta:
        # name that the controller is displayed at command line
        label = 'server'

        # text displayed next to the label in ``--help`` output
        description = 'The CloudBolt server plugin for IaaS'

        # stack this controller on-top of ``base`` (or any other controller)
        stacked_on = 'cloudbolt'

        # determines whether the controller is nested, or embedded
        stacked_type = 'nested'

        min_args = 3
        arguments = [
            (
                ['-E', '--environment'],
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
                ['-S', '--service'],
                dict(
                    help='Service',
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
            (
                ['-O', '--order'],
                dict(
                    help='Show order with this reference (id or href)',
                    action='store',
                )
            ),
            (
                ['-r', '--parameters'],
                dict(
                    help='Parameters for the service order',
                    action='store',
                )
            ),
            (
                ['-P', '--password'],
                dict(
                    help='Password for the new service',
                    action='store',
                )
            ),
            (
                ['-q', '--quantity'],
                dict(
                    help='Number of servers required (default=1)',
                    action='store',
                    default=1,
                )
            ),
            (
                ['-w', '--wait'],
                dict(
                    help='Minutes to wait for server(s) to be provisioned (default=120)',
                    action='store',
                    default=60,
                )
            ),
            (
                ['-z', '--sleep'],
                dict(
                    help='Minutes to wait between job status checks (default=2)',
                    action='store',
                    default=0.5,
                )
            ),
            (
                ['--all'],
                dict(
                    help='Show all servers',
                    action='store_true',
                )
            ),
            (
                ['--quick'],
                dict(
                    help='Show only basic server info',
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
        recipe = [
            {'parameter': 'service', 'description': 'The name of the service for the new server',       'ask': True, 'hint': 'Any name for the service chosen by the owner' },
            {'parameter': 'environment', 'description': 'The target environment for the new server',    'ask': True, 'hint': 'An Id or href for a valid environment. Refer to "environment list".', 'options': {
                'module': 'iaas.core.backend.cloudbolt.environments',
                'class': 'Environments',
                'method': 'list',
                'attribute': { 'show': ['id','name'], 'use': '_links/self/href', },
                'section': 'cloudbolt',
            } },
            {'parameter': 'blueprint', 'description': 'The blueprint for the new server',               'ask': True, 'hint': 'An Id or href for a valid blueprint. Refer to "blueprint list".', 'options': {
                'module': 'iaas.core.backend.cloudbolt.blueprints',
                'class': 'Blueprints',
                'method': 'list',
                'attribute': { 'show': ['id','name'], 'use': '_links/self/href', },
                'section': 'cloudbolt',
            } },
            {'parameter': 'group', 'description': 'The reference to a owner/ user group of the server', 'ask': True, 'hint': 'An Id or href for a valid group. Refer to "group list" or "user info".', 'options': {
                'module': 'iaas.core.backend.cloudbolt.groups',
                'class': 'Groups',
                'method': 'list',
                'attribute': { 'show': ['id','name'], 'use': '_links/self/href', },
                'section': 'cloudbolt',
            } },
            {'parameter': 'password', 'description': 'The login password for the new server',           'ask': True, 'hint': 'A password for the primary user in the newly provisioned server. Owner\'s choice.' },
            {'parameter': 'parameters', 'description': 'Additional (blueprint) parameters for the new server', 'ask': True, 'hint': 'Additional parameters for the newly provisioned server. Blueprint will dictate.' },
        ]

    @expose(help="List active CloudBolt servers (unless --all is used).")
    def list(self):
        if self.app._parsed_args.filters is None and not self.app._parsed_args.all and not self.app._parsed_args.quick:
            self.app._parsed_args.filters = 'status:ACTIVE,status:PROV'
            self.app.log.info('Setting filters to {}'.format(self.app._parsed_args.filters))
        if not self.app._parsed_args.quick:
            self.app._parsed_args.detailed=True
            self.app.log.debug('Not a --quick list. Asking for server details')
        servers = self._list(Servers(self.app.config.get_section_dict('cloudbolt')), parameters=self.app._parsed_args.__dict__)
        self.render(servers)

    @expose(help="Show what is required to create a new server")
    def recipe(self):
        self.app.log.info('Recipe: {}'.format(self._meta.recipe))
        self.render([self._meta.recipe])

    @expose(help="CloudBolt IaaS new server.")
    def create(self):
        self.app.log.info('Check the recipe')
        self.check_recipe()
        # if not self.app.pargs.group:
        #     raise IaaSError('Group is required')
        # if not self.app.pargs.blueprint:
        #     raise IaaSError('Blueprint is required')
        # if not self.app.pargs.environment:
        #     raise IaaSError('Environment is required')
        # if not self.app.pargs.parameters:
        #     raise IaaSError('Parameters is a required argument for provisioning a new service')
        self.app.log.info('Start the server create order')
        order = self._start_order(type='create')
        self.app.log.info('Add the build-items to the order')
        order.add(pargs=self.app._parsed_args.__dict__)
        self.app.log.info('Submit the order: {}'.format(order))
        self._submit_order(order)

    @expose(help="CloudBolt IaaS delete server.")
    def delete(self):
        recipe = [
            {'parameter': 'server', 'description': 'The target server',    'ask': True, 'hint': 'An Id or href for a server. Refer to "server list".', 'options': {
                'module': 'iaas.core.backend.cloudbolt.servers',
                'class': 'Servers',
                'method': 'list',
                'attribute': { 'show': ['hostname','status'], 'use': '_links/self/href', 'filters': [['status','ACTIVE']], 'alternatives': ['ip', '_links/self/title', '_links/self/href'] },
                'section': 'cloudbolt',
            } },
        ]
        self.app.log.info('Check the recipe')
        self.check_recipe(recipe=recipe)

        self.app.log.info('Start the server delete order')
        order = self._start_order(type='delete')
        self.app.log.info('Add the decom-items to the order')
        order.delete(pargs=self.app._parsed_args.__dict__)
        self.app.log.info('Submit the order: {}'.format(order))
        self._submit_order(order)

    @expose(help="CloudBolt current user info.")
    def describe(self):
        # if self.app._parsed_args.filters is None and not self.app._parsed_args.all and not self.app._parsed_args.quick:
        #     self.app._parsed_args.filters = 'status:ACTIVE,status:PROV'
        # if not self.app._parsed_args.quick:
        #     self.app._parsed_args.detailed=True
        recipe = [
            {'parameter': 'server', 'description': 'The target server',    'ask': True, 'hint': 'An Id or href for a server. Refer to "server list".', 'options': {
                'module': 'iaas.core.backend.cloudbolt.servers',
                'class': 'Servers',
                'method': 'list',
                'attribute': { 'show': ['hostname','status'], 'use': '_links/self/href', 'alternatives': ['ip', '_links/self/title', '_links/self/href'] },
                'section': 'cloudbolt',
            } },
        ]
        self.check_recipe(recipe=recipe)
        if getattr(self._meta, 'values', None):
            servers = self._meta.values
        else:
            servers = self._list(Servers(self.app.config.get_section_dict('cloudbolt')), parameters=self.app._parsed_args.__dict__)

        if self.app.pargs.server:
            self._filters = [string.split(self.app.pargs.server, ':')]
        servers = self._filter(servers)
        if len(servers) < 1:
            self.render([{'message': 'No servers found!'}])
            return
        self.render(servers)


def load(app):
    # register the plugin class.. this only happens if the plugin is enabled
    app.handler.register(CloudboltPluginServerController)
