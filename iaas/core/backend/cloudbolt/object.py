import json
import string
import traceback

from iaas.core.backend.cloudbolt.client import Client
from iaas.core.backend.cloudbolt.errors import IaaSCloudboltAPIError
from iaas.core.backend.object import IaaSObject
from iaas.core.exc import IaaSError


class IaaSCloudboltObject(IaaSObject):

    def __init__(self, config, *args, **kw):
        super(IaaSCloudboltObject, self).__init__(config, *args, **kw)
        [setattr(self, '_'+k, v) for k,v in kw.items()]
        if self.href():
            obj = self.retrieve(self._href, parameters=self.parameters)
            if isinstance(obj, dict):
                self.update(obj)
        else:
            pass
        pass

    def client(self):
        return Client(self.config)

    def retrieve(self, href, parameters=None):
        if parameters is None:
            parameters = {}
        respns = self.get_a_object(href, parameters)
        if isinstance(respns, basestring):
            respns = json.loads(respns)
        return respns

    def get_a_object(self, href, parameters=None):
        if parameters is None:
            parameters = {}
        resp = self.client().get_raw(href, headers=parameters.get('headers', None))
        try:
            if resp.status_code == 403:
                raise IaaSCloudboltAPIError(resp.status_code, 'GET {}: {}'.format(href, resp.text))
            if resp.status_code == 200:
                mash = json.loads(resp.text)
                return mash
            raise IaaSError('GET {}: {}'.format(href, resp.text))
        except IaaSCloudboltAPIError as e:
            return None
        except Exception as e:
            raise e

    def post_a_object(self, href, parameters=None):
        if parameters is None:
            parameters = {}
        resp = self.client().post(href, self, headers=parameters.get('headers', None), raw=parameters.get('raw', None))
        try:
            if resp.status_code == 403:
                raise IaaSCloudboltAPIError(resp.status_code, 'GET {}: {}'.format(href, resp.text))
            if resp.status_code == 200:
                mash = json.loads(resp.text)
                return mash
            raise IaaSError('GET {}: {}'.format(href, resp.text))
        except Exception as e:
            raise e

    def href(self, *args, **kw):
        if len(kw) > 0:
            [setattr(self, '_'+k, v) for k,v in kw.items()]
        if not hasattr(self,'_href'):
            if hasattr(self,'_id'):
                self._href = '/api/v2/{}/{}'.format(string.lower(self.__class__.__name__)+'s', self._id)
            else:
                # raise IaaSError('No href or id for %s' % str(self))
                if hasattr(self,'_ref'):
                    try:
                        if self._ref and self._ref == str(int(self._ref)):
                            self._id = int(self._ref)
                            return self.href()
                    except ValueError:
                        # Not an int
                        if self._ref[0] == '/':
                            self._href = self._ref
                if not getattr(self, '_href', None):
                    if self.has_key('_links') and self['_links'].has_key('self') and self['_links']['self'].has_key('href'):
                        self._href = self['_links']['self']['href']
                    else:
                        return None
        return self._href