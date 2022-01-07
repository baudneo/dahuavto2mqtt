import os
from typing import Optional

from requests.auth import HTTPDigestAuth

from common.consts import *


class DahuaConfigurationData:
    host: Optional[str]
    username: Optional[str]
    password: Optional[str]
    is_ssl: Optional[bool]
    auth: Optional[HTTPDigestAuth]

    def __init__(self):
        self.host = os.environ.get('DAHUA_VTO_HOST')
        self.is_ssl = str(os.environ.get('DAHUA_VTO_SSL', False)).lower() == str(True).lower()

        self.username = os.environ.get('DAHUA_VTO_USERNAME')
        self.password = os.environ.get('DAHUA_VTO_PASSWORD')

        self._auth = HTTPDigestAuth(self.username, self.password)
        self._base_url = f"{PROTOCOLS[self.is_ssl]}://{self.host}/cgi-bin/"

    @property
    def base_url(self):
        return self._base_url

    @property
    def auth(self):
        return self._auth
