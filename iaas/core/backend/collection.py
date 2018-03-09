import sys
import traceback

from iaas.core.exc import IaaSError


class IaaSCollection(list):

    def __init__(self, config, object_class):
        self.config = config
        self.object_class = object_class

    def get_a_page(self, object, *args, **kwargs):
        raise StandardError('Abstract base class invocation of '+__name__)

    def get_all_records(self, object, *args, **kwargs):

        try:
            parameters = kwargs.get('parameters', {})
            objs = []
            seen = 0
            try:
                pool = int(kwargs.get('pool', sys.maxint))
                if parameters.has_key('pool') and parameters['pool']:
                    pool = int(parameters['pool'])
            except ValueError as e:
                raise IaaSError("'limit' value is not an integer!?")
            try:
                total = int(kwargs.get('total', sys.maxint)) # Get all matches or the specified #
                if parameters.has_key('total') and parameters['total']:
                    total = int(parameters['total'])
            except ValueError as e:
                raise IaaSError("'limit' value is not an integer!?")
            # dater = parameters[:date_range] || 'all' # Get all matches or the specified #
            try:
                offset = int(kwargs.get('offset', 0))
                if parameters.has_key('offset') and parameters['offset']:
                    offset = int(parameters['offset'])
            except ValueError as e:
                raise IaaSError("'limit' value is not an integer!?")
            try:
                limit = int(kwargs.get('limit', 0))
                if parameters.has_key('limit') and parameters['limit']:
                    limit = int(parameters['limit'])
            except ValueError as e:
                raise IaaSError("'limit' value is not an integer!?")
            pn = 1
            try:
                if offset > 0:
                    pn = int(kwargs.get('page', offset/limit))
                if parameters.has_key('page') and parameters['page']:
                    pn = int(parameters['page'])
                else:
                    pn = int(kwargs.get('page', pn))
            except ValueError as e:
                raise IaaSError("'page' value is not an integer!?")

            page = self.get_a_page(object, action=kwargs.get('action', ''), pool=pool, total=total, page=pn, offset=offset, limit=limit)
            while page and isinstance(page, dict):
                if kwargs.get('_filter', None):
                    slice = []
                    for obj in page['_embedded']:
                        nobj = kwargs['_filter'](obj, kwargs['_collection'])
                        if not nobj is None:
                            slice.append(nobj)
                    objs.extend(slice)
                    seen += len(slice)
                else:
                    objs.extend(page['_embedded'])
                    seen += len(page['_embedded'])
                if page.has_key('count'): # Adjust limit (down or up) based on API feedback
                    limit = page['count']
                if page.has_key('total'): # Total is what API says or _everything_
                    if page['total'] < total:
                        total = page['total']
                    if page['total'] < pool:
                        pool = page['total']
                # pgnos = total/limit # No of pages is obvious
                if total < len(objs):
                    if isinstance(objs[0],list):
                        raise StandardError("Should not slice array of arrays")
                    objs = objs[0:total]

                next = False
                if page.has_key('_links'):
                    if page['_links'].has_key('next'):
                        next = True

                if next and len(objs) < total and seen < pool: # pn < pgnos &&
                    pn += 1
                    page = self.get_a_page(object, action=kwargs.get('action', ''), pool=pool, total=total, page=pn, offset=offset, limit=limit)
                else:
                    page = None
            return objs
        except IaaSError as e:
            raise e
        except Exception as e:
            traceback.print_exc(file=sys.stdout)

