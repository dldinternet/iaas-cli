import json
import string

import re

import datetime
from time import sleep

from iaas.core.backend.cloudbolt.blueprints import Blueprint
from iaas.core.backend.cloudbolt.client import Client
from iaas.core.backend.cloudbolt.collection import IaaSCloudboltCollection
from iaas.core.backend.cloudbolt.environments import Environment, Environments
from iaas.core.backend.cloudbolt.errors import IaaSCloudboltAPIError
from iaas.core.backend.cloudbolt.groups import Group, Groups
from iaas.core.backend.cloudbolt.jobs import Job
from iaas.core.backend.cloudbolt.object import IaaSCloudboltObject
from iaas.core.backend.cloudbolt.servers import Server, Servers
from iaas.core.backend.cloudbolt.services import Service
from iaas.core.backend.cloudbolt.users import Users
from iaas.core.exc import IaaSError


class Orders(IaaSCloudboltCollection):

    def __init__(self, config):
        super(Orders, self).__init__(config, Order)



class Order(IaaSCloudboltObject):

    def __init__(self, config, *args, **kw):
        super(Order, self).__init__(config, *args, **kw)

    def create(self, *args, **kwargs):
        varg = kwargs.get('pargs', None)
        if not varg:
            varg = kwargs
        group = None
        server = None
        type = varg.get('type', kwargs.get('type', None))
        resource = varg.get('resource', kwargs.get('resource', None))
        if type and type == 'delete':
            if not resource == 'service' or resource == 'server':
                servers = self._list_servers(kwargs, varg)
                for server in servers:
                    if not server is None:
                        group = Groups(self.config).find(ref=server['_links']['group']['href'])
                        if not group is None:
                            break
            elif resource == 'service':
                services = self._list_services(kwargs, varg)
                for service in services:
                    if not service is None:
                        group = Groups(self.config).find(ref=service['_links']['group']['href'])
                        if not group is None:
                            break
        if group is None:
            gid = varg.get('group', kwargs.get('group', None))
            if not gid:
                raise IaaSError('Server or Group is required to start an order.')
            groups = Groups(self.config).list(detailed=True)
            key = None
            try:
                if str(int(gid)) == gid:
                    key = 'id'
            except ValueError as e:
                if string.index(gid, '/') >= 0:
                    key = '_links/self/href'
            matches = groups._filter([[key, gid]])
            if isinstance(matches, list) and matches.__len__() > 0:
                group = matches[0]
        if not group is None: # This is NOT the else: for the previous statement ;)
            name = "Server order for {}".format(group._href)
            if not server is None:
                name = "Server order for {}".format(server._href)
            order_init = {
                "name": name,
                "group": group._href,
                "submit-now": "false"
            }
            resp = self.client().post('/api/v2/orders/', order_init, raw=True)
            if resp.status_code >= 400 or resp.status_code < 200:
                raise IaaSCloudboltAPIError(resp.text)
            else:
                mash = json.loads(resp.text)
                self.update(mash)
                return self
        else:
            raise IaaSError('Cannot determine/validate group')

    def _list_servers(self, kwargs, varg):
        if not getattr(self, '_servers', None):
            entries = re.split(',\s*', varg.get('server', kwargs.get('server', None)))
            servers = [self._server(kwargs, varg, ref=srvref) for srvref in entries]
            servers = [server for server in servers if not server is None]
            if servers.__len__() <= 0:
                raise IaaSError('Unable to find servers that match {}'.format(entries))
            self._servers = servers
        return self._servers

    def _list_services(self, kwargs, varg):
        if not getattr(self, '_services', None):
            entries = re.split(',\s*', varg.get('service', kwargs.get('service', None)))
            services = [self._service(kwargs, varg, ref=svc) for svc in entries]
            services = [service for service in services if not service is None]
            if services.__len__() <= 0:
                raise IaaSError('Unable to find services that match {}'.format(entries))
            self._services = services
        return self._services

    def add(self, *args, **kwargs):
        varg = kwargs.get('pargs', None)
        if not varg:
            varg = kwargs
        bpref = varg.get('blueprint', kwargs.get('blueprint', None))
        if not bpref:
            raise IaaSError('blueprint is required to add to an order.')
        if not isinstance(bpref, Blueprint):
            blueprint = Blueprint(self.config, ref=bpref)
            if not blueprint:
                raise IaaSError('Unable to find blueprint {}'.format(bpref))
        else:
            blueprint = bpref

        if not blueprint.get('is-orderable', False):
            raise IaaSError('Blueprint {} is not orderable'.format(bpref))

        parameters = varg.get('parameters', kwargs.get('parameters', None))
        sections = {}
        if parameters and len(string.lstrip(string.rstrip(parameters))) > 0:
            kv = lambda x: re.split('=\s*', x)
            # pm = lambda x: re.split(',\s*', x)
            sn = lambda x: re.split(':\s*', x)
            if string.find(parameters, ':') < 0:
                raise IaaSError('Invalid blueprint parameters: {} (Missing : so not able to identify build item)'.format(parameters))
            if string.find(parameters, '=') < 0:
                raise IaaSError('Invalid blueprint parameters: {} (Missing = so not able to identify key/value pairs)'.format(parameters))
            raw_sects = re.split(';\s*', parameters)
            raw_sects = dict(map(sn,raw_sects))
            for sect,pars in raw_sects.items():
                assigns = re.split(',\s*', pars)
                parameters = map(kv, assigns)
                parameters = dict(parameters)
                sections[sect] = parameters
        service_name = varg.get('service', kwargs.get('service', None))
        if not service_name:
            raise IaaSError('Service name is required to add to an order.')
        environment = self._environment(kwargs, varg)
        password = varg.get('password', kwargs.get('password', None))
        if not password:
            raise IaaSError('Password is required to add to a service order.')
        if password.__len__() < 8:
            raise IaaSError('Password must be 8 characters or more to add to a service order.')

        blueprint_items_arguments = {}

        for item in blueprint['build-items']:
            name = "build-item-{}".format(item['name'])
            parameters = sections.get(item['name'], {})
            if item['type'] == 'provserver':
                parameters.update({
                    "new-password": password
                })
                build_item = {
                    "environment": environment._href,
                    "attributes": {
                        "quantity": varg.get('quantity', kwargs.get('quantity', 1))
                    },
                    "parameters": parameters
                }
            else:
                build_item = {
                    "parameters": parameters,
                }
            blueprint_items_arguments[name] = build_item

        order_service_item = {
            "blueprint": blueprint._href,
            "blueprint-items-arguments": blueprint_items_arguments,
            "service-name": service_name
        }

        resp = self.client().post(self.href()  + '/deploy-items/', order_service_item, raw=True)
        if resp.status_code >= 400 or resp.status_code < 200:
            raise IaaSCloudboltAPIError(resp.text)
        else:
            mash = json.loads(resp.text)
            self.update(mash)
            return self


    def delete(self, *args, **kwargs):
        varg = kwargs.get('pargs', None)
        if not varg:
            varg = kwargs

        environment = None
        servers = None
        services = None
        resource = varg.get('resource', kwargs.get('resource', None))
        if not resource == 'service' or resource == 'server':
            servers = self._list_servers(kwargs, varg)
            for server in servers:
                if not server.get('status', None) in ['ACTIVE', 'PROV']:
                    raise IaaSError('Server {} is not ACTIVE'.format(server._href))

                if server:
                    environment = Environments(self.config).find(ref=server['_links']['environment']['href'])
                if environment is None:
                    if not kwargs['environment']:
                        raise IaaSError('Server or Environment is required to start a delete order.')
                    environment = self._environment(kwargs, varg)
                if not environment is None:
                    break
        elif resource == 'service':
            services = self._list_services(kwargs, varg)
            for service in services:
                if not service.get('status', None) in ['Active']:
                    raise IaaSError('Service {} is not Active'.format(service._href))

                if service:
                    server = None
                    if service['_links']['servers'].__len__() > 0:
                        server = Servers(self.config).find(ref=service['_links']['servers'][0]['href'])
                    else:
                        servers = Servers(self.config).list(detailed=True)
                        if servers.__len__() > 0:
                            server = servers[0]
                    if server:
                        environment = Environments(self.config).find(ref=server['_links']['environment']['href'])
                    if environment is None:
                        if not kwargs['environment']:
                            raise IaaSError('Service or Environment is required to start a delete order.')
                        environment = self._environment(kwargs, varg)
                    if not environment is None:
                        break

        if not environment is None:

            decom_item = {}
            decom_item['environment'] = environment._href
            if not resource == 'service' or resource == 'server':
                decom_item['servers']     = [server._href for server in servers]
            elif resource == 'service':
                decom_item['services']     = [service._href for service in services]

            resp = self.client().post(self.href()  + '/decom-items/', decom_item, raw=True)
            if resp.status_code >= 400 or resp.status_code < 200:
                raise IaaSCloudboltAPIError(resp.text)
            else:
                mash = json.loads(resp.text)
                self.update(mash)
                return self
        else:
            raise IaaSError('Cannot determine/validate environment')

    def _server(self, kwargs, varg, ref=None):
        if ref is None:
            ref = varg.get('server', kwargs.get('server', None))
        if not ref:
            raise IaaSError('server is required to add to a delete order.')
        if not isinstance(ref, Server):
            if not getattr(self, '_collection', None):
                self._collection = Servers(self.config)
            server = Server(self.config, ref=ref)
            if not (server is None or server.href()):
                server = self._collection.find(ref=ref)
                # if not (server is None or server.href()):
                #     raise IaaSError('Unable to find server {}'.format(srvref))
            ref = server
        return ref

    def _service(self, kwargs, varg, ref=None):
        if ref is None:
            ref = varg.get('service', kwargs.get('service', None))
        if not ref:
            raise IaaSError('service is required to add to a delete order.')
        if not isinstance(ref, Server):
            if not getattr(self, '_collection', None):
                self._collection = Servers(self.config)
            service = Service(self.config, ref=ref)
            if not (service is None or service.href()):
                service = self._collection.find(ref=ref)
                # if not (service is None or service.href()):
                #     raise IaaSError('Unable to find service {}'.format(srvref))
            ref = service
        return ref

    def _environment(self, kwargs, varg):
        envref = varg.get('environment', kwargs.get('environment', None))
        if not envref:
            raise IaaSError('Environment is required to add to an order.')
        if not isinstance(envref, Environment):
            environment = Environment(self.config)
            environment.href(ref=envref)
        else:
            environment = envref
        return environment

    def submit(self, *args, **kwargs):
        def checkstatus(self):
            if not (self['status'] == 'PENDING' or self['status'] == 'CART'):
                resp = {'status_code': 500, 'detail': 'Order status error', 'error': "Order {}: Only orders that are in 'PENDING' state can be approved. Current state of order is {}".format(self._href, self['status'])}
                resp.update({'_links': self['_links']})
                return resp
            return None

        def checkresponse(self, resp):
            if resp.status_code == 200:
                mash = json.loads(resp.text)
                self.update(mash)
                return mash
            raise IaaSCloudboltAPIError(resp.status_code, resp.text)

        mash = self._action('submit', checkstatus, checkresponse)
        if not mash is None:
            return mash
        raise IaaSError('Order {} cannot be cancelled'.format(self._href))

    def _action(self, verb, checkstatus, checkresponse):
        if self['_links'].has_key('actions'):
            actions = [action for action in self['_links']['actions'] if action.has_key(verb)]
            if not len(actions) > 0:
                raise IaaSError('Order {} has no "{}" action'.format(self._href, verb))
            action = actions[0]
        else:
            self.update(Order(self.config, href=self._href))
            action = {verb: {'href': self._href + '/actions/{}'.format(verb)}}
        if self.get('status', None):
            resp = checkstatus(self)
            if not resp is None:
                return resp
        resp = self.client().post(action[verb]['href'], raw=True)
        if resp.status_code >= 400 or resp.status_code < 200:
            return checkresponse(self, resp)
        else:
            # return json.loads(resp.text)
            mash = json.loads(resp.text)
            self.update(mash)
            return self

    def cancel(self):
        def checkstatus(self):
            if not (self['status'] == 'PENDING' or self['status'] == 'CART'):
                resp = {'status_code': 500, 'detail': 'Order status error', 'error': "Order {}: Only orders that are in 'PENDING' state can be approved. Current state of order is {}".format(self._href, self['status'])}
                resp.update({'_links': self['_links']})
                return resp
            return None

        def checkresponse(self, resp):
            if resp.status_code == 200 or (resp.status_code == 500 and verb == 'submit'):
                # A failed submit is ok when we 'cancel'
                mash = json.loads(resp.text)
                mash.update({'_links': self['_links']})
                mash['detail'] = "Order {} was {}'ed".format(self._href,verb)
                mash['status_code'] = 200 # Fake it
                mash.pop('error')
                return mash
            if resp.status_code == 404:
                # Ok the first link does not work ...
                return None
            else:
                raise IaaSCloudboltAPIError(resp.text)

        for verb in ['cancel', 'submit']:
            mash = self._action(verb, checkstatus, checkresponse)
            if not mash is None:
                return mash
        raise IaaSError('Order {} cannot be cancelled'.format(self._href))
