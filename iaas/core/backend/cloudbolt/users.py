import json
import string

from iaas.core.backend.cloudbolt.client import Client
from iaas.core.backend.cloudbolt.collection import IaaSCloudboltCollection
from iaas.core.backend.cloudbolt.object import IaaSCloudboltObject
from iaas.core.exc import IaaSError


class Users(IaaSCloudboltCollection):

    def __init__(self, config):
        super(Users, self).__init__(config, User)

    def list(self):
        try:
            respns = self.get('/users')
            return respns
        except Exception as e:
            raise IaaSError(str(e.message))


    def me(self):
        try:
            users = self.list()
            info = [user for user in users if string.lower(user['user.username']) == self.config.get('username')]
            if not isinstance(info, list):
                raise IaaSError('User info returned is incorrect type(%s): %s' % (info.__class__.__name__, info))
            if len(info) < 1:
                return None
            me = User(self.config, href=info[0]['_links']['self']['href'])
            return me
        except Exception as e:
            raise IaaSError(str(e.message))


class User(IaaSCloudboltObject):

    def __init__(self, config, *args, **kw):
        super(User, self).__init__(config, *args, **kw)
