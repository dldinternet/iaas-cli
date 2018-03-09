import json
import sys
import traceback
import requests
import urllib3
urllib3.disable_warnings()
# import logging
# logging.captureWarnings(True)

class CloudBoltAPIError(StandardError):
    pass

class CloudBoltAPIClient:

    def __init__(self, username, password, host="localhost",
                 port=80, protocol="http"):
        """
        Creates base URL and auth required for rest calls.
        """
        self.BASE_URL = "{protocol}://{host}:{port}".format(
            protocol=protocol, host=host, port=port)
        self.username = username
        self.password = password

    def _get_token(self):
        """
        Get a bearer token for API calls.
        """
        try:
            get_token = requests.post(self.BASE_URL + "/api/v2/api-token-auth/",
                                      json={"username": self.username, "password": self.password},
                                      verify=False,
                                      headers={'Content-Type': 'application/json'})
            if get_token.status_code != 200:
                raise CloudBoltAPIError(get_token.text)
            token = json.loads(get_token.content)
        except Exception as e:
            # app.log.fatal('Uncaught Exception > %s: %s' % (e.__class__, e.message))
            traceback.print_exc(file=sys.stdout)
            raise e
        return token["token"]

    def _headers(self, headers=None):
        if not headers:
            # By default, requests should be parsed as JSON; however do not set
            # this for file uploads or they'll break.
            headers = {'Content-Type': "application/json"}

        token = self._get_token()
        headers['authorization'] = "Bearer " + token
        return headers

    def _request(self, uri, headers=None, raw=False):
        """
        Make a request of the specified method and return the text response.
        """

        response = requests.get(self.BASE_URL + uri,
                                verify=False,
                                headers=self._headers(headers))
        if raw:
            return response
        else:
            return response.text

    def _post_request(self, url, data="", headers=None, raw=False):
        response = requests.post(self.BASE_URL + url,
                                 data=json.dumps(data),
                                 verify=False,
                                 headers=self._headers(headers))
        if raw:
            return response
        else:
            return response.text

    def get(self, uri="", headers=None, raw=False):
        """
        Simple GET entry point
        """
        uri = self._fix_uri(uri)
        return self._request(uri, headers=headers, raw=raw)

    def get_raw(self, url, headers=None):
        """
        Make a GET request and return the raw response object.  For more about
        that object, see:
        http://docs.python-requests.org/en/latest/api/#requests.Response.raw
        """
        url = self._fix_uri(url)
        return self._request(url, headers, True)

    def post(self, url, body="", headers=None, raw=False):
        """
        Simple POST entry point
        """
        url = self._fix_uri(url)

        return self._post_request(url, body, headers=headers, raw=raw)

    def delete(self, url):
        """
        Simple DELETE entry point
        """
        url = self._fix_uri(url)

        return self._request("DELETE", url)

    def _fix_uri(self, uri):
        split = uri.split("?")
        uri = split[0]
        if not uri.endswith('/'):
            uri = "{url}/".format(url=uri)
        if not uri.startswith('/api/v2'):
            uri = '/api/v2' + uri
        params = ''
        if len(split) >= 2:
            params = '?'+ "&".join(split[1:] or '')
        args = {
            "uri": uri,
            "params": params
        }
        return "{uri}{params}".format(**args)
