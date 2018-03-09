"""CloudboltPlugin for IaaS."""
import string
import os
from cement.ext.ext_argparse import expose
from iaas.core.backend.cloudbolt.groups import Groups, Group
from iaas.core.exc import IaaSError
from ..cloudbolt import CloudboltPluginController


class CloudboltPluginGroupController(CloudboltPluginController):
    class Meta:
        # name that the controller is displayed at command line
        label = 'group'

        # text displayed next to the label in ``--help`` output
        description = 'The CloudBolt group plugin for IaaS'

        # stack this controller on-top of ``base`` (or any other controller)
        stacked_on = 'cloudbolt'

        # determines whether the controller is nested, or embedded
        stacked_type = 'nested'

        # these arguments are only going to display under
        # ``$ iaas cloudbolt group --help``
        min_args = 3
        arguments = [
            (
                ['-G', '--group'],
                dict(
                    help='Group href or id',
                    action='store',
                )
            ),
        ]


    @expose(help="CloudBolt Groups list IaaS sub-command.")
    def list(self):
        groups = self._list(Groups(self.app.config.get_section_dict('cloudbolt'), parameters=self.app._parsed_args.__dict__))
        self.render(groups)

    @expose(help="CloudBolt current group info.")
    def info(self):
        groups = Groups(self.app.config.get_section_dict('cloudbolt')).list()
        info = [group for group in groups if string.lower(group['group.groupname']) == self.app.config.get('cloudbolt', 'groupname')]
        if not isinstance(info, list):
            raise IaaSError('Group info returned is incorrect type(%s): %s' % (info.__class__, info))
        me = Group(self.app.config.get_section_dict('cloudbolt'), href=info[0]['_links']['self']['href'])
        self.render([me])

    @expose(help="CloudBolt show select attributes of current group.")
    def show(self):

        def getid(rec):
            pass

        groups = Groups(self.app.config.get_section_dict('cloudbolt')).list()
        info = [group for group in groups if string.lower(group['group.groupname']) == self.app.config.get('cloudbolt', 'groupname')]
        if not isinstance(info, list):
            raise IaaSError('Group info returned is incorrect type(%s): %s' % (info.__class__, info))
        me = [Group(self.app.config.get_section_dict('cloudbolt'), href=info[0]['_links']['self']['href'])]
        if len(me) > 0:
            attributes = []
            if self.app.pargs.self:
                attributes.append('_links/self')
            if self.app.pargs.groups:
                # attributes.append('_links/groups/(href;title)')
                attributes.append('_links/groups')
            if self.app.pargs.id:
                attributes.append(getid)
            if len(attributes) > 0:
                if self.app.pargs.attributes:
                    self.app.pargs.attributes += ','.join(attributes)
                else:
                    self.app.pargs.attributes = ','.join(attributes)

            if self.app.pargs.attributes:
                nume = self._prune(me, 'attributes')
                if len(nume) > 0:
                    me = nume
                else:
                    me = [{"message": 'No group attributes matched from "{}"'.format(self.app.pargs.attributes)}]
        else:
            me = [{"message": 'No groups found'}]
        self.render(me)


def load(app):
    # register the plugin class.. this only happens if the plugin is enabled
    app.handler.register(CloudboltPluginGroupController)
