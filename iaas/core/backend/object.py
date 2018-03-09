import string

import re

from iaas.core.exc import IaaSError


class IaaSObject(dict):

    def __init__(self, config, *args, **kw):
        super(IaaSObject, self).__init__()
        # self.data = {}
        self.config = config
        self.parameters = kw.get('parameters', None)

    def get_a_object(self, href, *args, **kwargs):
        raise StandardError('Abstract base class invocation of '+__name__)


    def _evaluate(self, flt, against=None):
        if against is None:
            against=self
        if isinstance(flt, basestring):
            try:
                if isinstance(against, dict):
                    idx = string.index(flt, '/')
                    parts = string.split(flt, '/')
                    return self._match_parts(parts, against)
                else:
                    if isinstance(against, list):
                        val = [o._evaluate(flt) for o in against]
                        val = [o for o in val if o]
                        return val
                    else:
                        if isinstance(against, basestring):
                            return against
                        else:
                            raise IaaSError('What to do about a {}'.format(against.__class__.__name__))
            except ValueError as e:
                return self._match_parts([flt], against)
        else:
            if isinstance(flt, basestring):
                return against.has_key(flt)
        return None

    def _match_parts(self, parts, against):
        if against is None:
            against=self
        matches = re.match('^\((.*?)\)$', parts[0])
        if matches:
            flds = string.split(matches.group(1), ';')
            if isinstance(against, dict):
                no = self.__class__(self.config, parameters=self.parameters)
                for k in flds:
                    if against.has_key(k):
                        no[k] = against[k]
                if len(no) <= 0:
                    return None
                return no
            else:
                raise IaaSError('TODO {}'.format(against.__class__.__name__))
        else:
            if not against.has_key(parts[0]):
                return None
            if len(parts) == 1:
                return against[parts[0]]
            return self._evaluate('/'.join(parts[1:]), against=against[parts[0]])
