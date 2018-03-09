"""Cloudbolt Plugin for IaaS."""
import re
import string
import sys
from collections import OrderedDict

import datetime
from time import sleep

from iaas.cli.controllers.backend import IaaSBackendAbstractController
from iaas.core.backend.cloudbolt.collection import IaaSCloudboltCollection
from iaas.core.backend.cloudbolt.errors import IaaSCloudboltAPIError
from iaas.core.backend.cloudbolt.jobs import Job
from iaas.core.backend.cloudbolt.object import IaaSCloudboltObject
from iaas.core.backend.cloudbolt.orders import Order
from iaas.core.exc import IaaSError


class CloudboltPluginController(IaaSBackendAbstractController):
    class Meta:
        # name that the controller is displayed at command line
        label = 'cloudbolt'

        # text displayed next to the label in ``--help`` output
        description = 'The CloudBolt plugin for IaaS'

        # stack this controller on-top of ``base`` (or any other controller)
        stacked_on = 'base'

        # determines whether the controller is nested, or embedded
        stacked_type = 'nested'

        # these arguments are only going to display under
        # ``$ iaas cloudbolt --help``
        common_arguments = [
            (
                ['-c', '--columns'],
                dict(
                    help='Columns',
                    action='store',
                    )
            ),
            (
                ['-d', '--detailed', '--details'],
                dict(
                    help='Detailed list',
                    action='store_true',
                    )
            ),
            (
                ['-f', '--filters'],
                dict(
                    help='Filters',
                    action='store',
                    )
            ),
            (
                ['-n', '--total'],
                dict(
                    help='Number of items to list',
                    action='store',
                )
            ),
            (
                ['-l', '--limit'],
                dict(
                    help='Number of items to list per page',
                    action='store',
                )
            ),
            (
                ['-p', '--page'],
                dict(
                    help='Page number of items to list',
                    action='store',
                )
            ),
            (
                ['-a', '--attributes'],
                dict(
                    help='Attributes to show',
                    action='store',
                )
            ),
            (
                ['-L', '--log-level', '--log_level'],
                dict(
                    help='Desired application log level',
                    action='store'
                )
            ),
            (
                ['--log-file', '--log_file'],
                dict(
                    help='Desired application log file',
                    action='store',
                )
            ),
            (
                ['--log-console', '--log_console'],
                dict(
                    help='Log to console',
                    action='store_true',
                )
            ),
        ]

        min_args = 3

        table_format = 'psql'
        headers = 'keys'


    def __init__(self, *args, **kw):
        if self.__class__.__name__ != 'CloudboltPluginController':
            if not getattr(self.Meta, 'arguments_inherited', False):
                self.Meta.arguments = self.Meta.arguments + CloudboltPluginController.Meta.common_arguments
                self.Meta.arguments_inherited = True
                seen = {}
                for arg in self.Meta.arguments:
                    if arg[0].__len__() >= 2:
                        word = arg[0][1]
                    else:
                        word = arg[0][0]
                    if not seen.get(word, False):
                        seen[word] = True
                    else:
                        raise IaaSError("arg {} is duplicated in {}".format(arg, self.__class__.__name__))
            else:
                pass
        super(CloudboltPluginController, self).__init__(*args, **kw)
        self._client = None

    def _show(self, collection, *args, **kwargs):
        self.render(self._find(collection, *args, **kwargs))

    def _find(self, collection, *args, **kwargs):
        list = self._list(collection, *args, **kwargs)
        obj = collection.object_class(self.app.config.get_section_dict('cloudbolt'))
        obj_href = obj.href(ref=kwargs['ref'])
        if obj_href:
            list = [obj for obj in list if obj['_links']['self']['href'] == obj_href]
        return list

    def _list(self, collection, *args, **kwargs):
        if self.app.pargs.filters:
            kwargs['_filter'] = self._weigh
            kwargs['_collection'] = collection
        resp = collection.list(*args, **kwargs)

        if not self.app.pargs.filters:
            nrsp = []
            for obj in resp:
                nobj = collection.object_class(self.app.config.get_section_dict('cloudbolt'))
                if kwargs.get('detailed', False) or self.app.pargs.detailed:
                    try:
                        nobj = collection.object_class(self.app.config.get_section_dict('cloudbolt'), href=obj['_links']['self']['href'])
                    except IaaSCloudboltAPIError as e:
                        if e.status_code != 403:
                            raise e
                        else:
                            nobj['details'] = 'Permission for details denied'
                nobj.href(href=obj['_links']['self']['href'])
                nobj.update(obj)
                nrsp.append(nobj)
            resp = self._filter(nrsp)
        return self._prune(resp)

    def _weigh(self, obj, collection=None):
        if not collection is None and isinstance(collection, IaaSCloudboltCollection) and not isinstance(obj, IaaSCloudboltObject):
            nobj = collection.object_class(self.app.config.get_section_dict('cloudbolt'), href=obj['_links']['self']['href'])
            obj.update(nobj) # So that nobj attributes override
            nobj.update(obj) # To inherite missing
            obj = nobj # To return
        if not self.filters() or collection is None or not isinstance(collection, IaaSCloudboltCollection):
            return obj
        return collection._weigh(obj, self.filters())


    def _start_order(self, *args, **kw):
        order = Order(self.app.config.get_section_dict('cloudbolt'))
        self.app.log.info('Create a new order" {}'.format(self.app._parsed_args.__dict__))
        return order.create(pargs=self.app._parsed_args.__dict__, *args, **kw)

    def _submit_order(self, order):
        start_time = datetime.datetime.now()
        self.app.log.info('Submitting order at {}'.format(start_time))
        order.submit()
        orders = self._watch_order(order=order, pargs=self.app._parsed_args.__dict__, config=self.app.config, start_time=start_time)
        self.app.log.info('Render results')
        self.render(orders)


    def _watch_order(self, order=None, pargs=None, config=None, start_time=None):
        self.app.log.info('Watch the order {}'.format(order))
        if order['status'] != 'ACTIVE':
            self.app.log.error('The order is not ACTIVE. Do not know what went wrong')
            return [order]
        # Create While loop to check the order status and then return the server names once the order is complete.
        if start_time is None:
            start_time = datetime.datetime.now()
        wait = datetime.timedelta(minutes=float(pargs.get('wait', 0.5)))
        self.app.log.info('Wait {} for order to complete'.format(wait))
        slpt = float(pargs.get('sleep', 0.5)) * 60
        self.app.log.info('Wait {} seconds between checks'.format(slpt))
        orders = []
        finished = False
        while not finished:
            elapsed = datetime.datetime.now()-start_time
            check = Order(config.get_section_dict('cloudbolt'), href=order._href)
            if check["status"] == "ACTIVE" and elapsed < wait:
                finished = False
                msg = "Order {} is ACTIVE for {:6.2f} seconds. Waiting {} seconds for order to complete ...".format(order._href, elapsed.total_seconds(),slpt)
                print(msg)
                self.app.log.info(msg)
                # Typical job takes twelve (12) minutes to complete, so we increased the sleep time to 120 seconds.
                sleep(slpt)
            elif elapsed >= wait:
                # Added a time constraint to the loop for run away jobs.
                msg="Job has not completed within the {} minutes time limit".format(wait)
                self.app.log.error(msg)
                print(msg)
                exit(1)
            else:
                self.app.log.info("Order {} Status: {}".format(check._href, check["status"]))
                for job_ref in check['_links']['jobs']:
                    job = Job(config.get_section_dict('cloudbolt'), href=job_ref['href'])
                    if not job.get('output', None):
                        job['output'] = ''
                    self.app.log.info('Job {} {} Status: {} {}'.format(job._href, job['type'], job['status'], job['output']))
                    # if job['type'] == 'Provision Server' or job['type'] == 'Delete Server':
                    #     server_list.append(job['output'].split('hostname')[1].split(".")[0].strip())
                orders.append(check)
                break

        if len(orders) == 0:
            orders = [{'message': 'No orders completed this run'}]
        return orders
