import json
import string
import sys
import traceback

import re

from iaas.core.backend.cloudbolt.client import Client
from iaas.core.backend.cloudbolt.errors import IaaSCloudboltAPIError
from iaas.core.backend.collection import IaaSCollection
from iaas.core.exc import IaaSError


class IaaSCloudboltCollection(IaaSCollection):

    def __init__(self, config, object_class):
        super(IaaSCloudboltCollection, self).__init__(config, object_class)

    def client(self):
        return Client(self.config)

    def get(self, object, *args, **kwargs):
        respns = self.get_all_records(object, *args, **kwargs)
        if isinstance(respns, basestring):
            try:
                respns = json.loads(respns)
            except Exception as e:
                raise e
        try:
            detailed = kwargs.get('detailed', False)
            nrspns = []
            for obj in respns:
                if detailed:
                    nobj = self.object_class(self.config, ref=obj['_links']['self']['href'])
                else:
                    nobj = self.object_class(self.config)
                obj.update(nobj)
                nobj.update(obj)
                nrspns.append(nobj)
            respns = nrspns
        except KeyError:
            pass
        self.extend(respns)
        return self

    def get_a_page(self, object, *args, **kwargs):
        resp = self.client().get("%s/%s?page=%d" %(object, kwargs.get('action', ''), kwargs.get('page', 1)), headers=kwargs.get('headers'), raw=kwargs.get('raw'))
        try:
            mash = json.loads(resp)
        except Exception as e:
            raise e
        return mash

    # def list(self, *args, **kwargs):
    #     raise IaaSError('{} is an abstract class'.format(__name__))

    def list(self, *args, **kw):
        try:
            if not self.__len__() > 0:
                self.get('/{}'.format(string.lower(self.__class__.__name__)), *args, **kw)
            return self
        except Exception as e:
            raise IaaSError(str(e.message))

    def find(self, *args, **kw):
        kw['ref'] = kw.get('ref', kw.get(string.lower(self.object_class.__name__), None))
        try:
            obj = self.object_class(self.config, None, ref=kw.get('ref', None))
            if not obj.href():
                parts = string.split(obj._ref, ':')
                if len(parts) >= 2:
                    kv = lambda x: re.split(':\s*', x)
                    filters = re.split(',\s*', obj._ref)
                    filters = map(kv, filters)
                    self.list(detailed=True)
                    matches = self._filter(filters)
                    if matches.__len__() > 0:
                        obj = matches[0]
                    else:
                        obj = None
                else:
                    obj = None
        except IaaSCloudboltAPIError as e:
            obj = self.object_class(self.config, None)
            obj.href(ref=kw.get('ref', None))
        return obj

    def _weigh(self, obj, filters):
        for flt in filters:
            if not isinstance(obj, self.object_class):
                nobj = self.object_class(self.config)
                nobj.update(obj)
                obj = nobj
            val = obj._evaluate(flt[0])
            if not val is None:
                if val == flt[1]:
                    return obj
            else:
                return obj
        return None

    def _filter(self, filters=None):
        if filters:
            list = self.__class__(self.config)
            for obj in self:
                if self._weigh(obj, filters):
                    list.append(obj)
            return list
        else:
            return self
