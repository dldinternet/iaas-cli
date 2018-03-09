from ConfigParser import NoOptionError
from iaas.core.exc import IaaSError
from iaas.vendor.cloudbolt.api_client import CloudBoltAPIClient


class Client:

    _client = None

    def __init__(self, config):
        self.config = config
        if Client._client is None:
            Client._client = self.api_client()
        if not isinstance(Client._client, CloudBoltAPIClient):
            raise ValueError('Cannot obtain API client for %s' % __name__)

    def api_client(self):
        try:
            config = self.config
            protocol = config.get('protocol') or 'https'
            port = config.get('port') or 443

            domain = config.get('domain')
            username = config.get('username') + '@' + domain
            password = config.get('password')
            hostname = config.get('hostname')

            return CloudBoltAPIClient(username, password, host=hostname, port=port, protocol=protocol)
        except NoOptionError as e:
            raise IaaSError(str(e.message))

    def __getattr__(self, name):
        return getattr(self._client, name)
