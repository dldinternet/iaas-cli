import json

from iaas.core.backend.cloudbolt.client import Client
from iaas.core.backend.cloudbolt.collection import IaaSCloudboltCollection
from iaas.core.backend.cloudbolt.errors import IaaSCloudboltAPIError
from iaas.core.backend.cloudbolt.object import IaaSCloudboltObject
from iaas.core.backend.cloudbolt.users import Users
from iaas.core.exc import IaaSError


class Groups(IaaSCloudboltCollection):

    def __init__(self, config):
        super(Groups, self).__init__(config, Group)

    def find(self, *args, **kw):
        kw['ref'] = kw.get('ref', kw.get('group', None))
        try:
            group = Group(self.config, None, ref=kw.get('ref', None))
            if not group.href():
                return self.find_my_group(*args, **kw)
            return group
        except IaaSCloudboltAPIError as e:
            return self.find_my_group(*args, **kw)

    def find_my_group(self, *args, **kw):
        me = Users(self.config).me()
        group = Group(self.config, None)
        group_href = group.href(ref=kw.get('ref', None))
        groups = [group['href'] for group in me['_links']['groups'] if group['href'] == group_href]
        if len(groups) > 0:
            group = groups[0]
            obj = Group(self.config, None)
            obj.href(ref=group)
            group = obj
        else:
            group = None
        return group


class Group(IaaSCloudboltObject):

    def __init__(self, config, *args, **kw):
        super(Group, self).__init__(config, *args, **kw)
