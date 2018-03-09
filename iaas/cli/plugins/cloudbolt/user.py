"""CloudboltPlugin for IaaS."""
import string
import os
from cement.ext.ext_argparse import expose
from iaas.core.backend.cloudbolt.users import Users, User
from iaas.core.exc import IaaSError
from ..cloudbolt import CloudboltPluginController


class CloudboltPluginUserController(CloudboltPluginController):
    class Meta:
        # name that the controller is displayed at command line
        label = 'user'

        # text displayed next to the label in ``--help`` output
        description = 'The CloudBolt user plugin for IaaS'

        # stack this controller on-top of ``base`` (or any other controller)
        stacked_on = 'cloudbolt'

        # determines whether the controller is nested, or embedded
        stacked_type = 'nested'

        # these arguments are only going to display under
        # ``$ iaas cloudbolt user --help``
        min_args = 3
        arguments = [
            (
                ['-g', '--groups'],
                dict(
                    help='Groups',
                    action='store_true',
                )
            ),
            (
                ['-s', '--self'],
                dict(
                    help='Self',
                    action='store_true',
                )
            ),
        ]


    @expose(help="CloudBolt Users list IaaS sub-command.")
    def list(self):
        users = self._list(Users(self.app.config.get_section_dict('cloudbolt')), parameters=self.app._parsed_args.__dict__)
        self.render(users)

    @expose(help="CloudBolt current user info.")
    def info(self):
        me = Users(self.app.config.get_section_dict('cloudbolt')).me()
        self.render([me])

    @expose(help="CloudBolt show select attributes of current user.")
    def show(self):

        def getid(rec):
            pass

        me = [Users(self.app.config.get_section_dict('cloudbolt')).me()]
        # info = [user for user in users if string.lower(user['user.username']) == self.app.config.get('cloudbolt', 'username')]
        # if not isinstance(info, list):
        #     raise IaaSError('User info returned is incorrect type(%s): %s' % (info.__class__, info))
        # me = [User(self.app.config.get_section_dict('cloudbolt'), href=info[0]['_links']['self']['href'])]
        if len(me) > 0:
            attributes = []
            if getattr(self.app.pargs, 'self', None):
                attributes.append('_links/self')
            if getattr(self.app.pargs, 'groups', None):
                # attributes.append('_links/groups/(href;title)')
                attributes.append('_links/groups')
            if getattr(self.app.pargs, 'id', None):
                attributes.append(getid)
            if len(attributes) > 0:
                if getattr(self.app.pargs, 'attributes', None):
                    self.app.pargs.attributes += ','.join(attributes)
                else:
                    self.app.pargs.attributes = ','.join(attributes)

            if getattr(self.app.pargs, 'attributes', None):
                nume = self._prune(me, 'attributes')
                if len(nume) > 0:
                    me = nume
                else:
                    me = [{"message": 'No user attributes matched from "{}"'.format(self.app.pargs.attributes)}]
        else:
            me = [{"message": 'No users found'}]
        self.render(me)


def load(app):
    # register the plugin class.. this only happens if the plugin is enabled
    app.handler.register(CloudboltPluginUserController)
