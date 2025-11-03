import re
from urllib.request import urlopen
from lib.params import Params

"""
Text File Datasource: checks telegram login against a plain text file available by URL.
Each line should contain one username (with or without leading '@').
"""

class ReaderFile:
    config = {}

    params = {'location': {'type': str}}

    def __init__(self, config):
        if config:
            self.config = config

    async def check_allowed_user(self, location, username):
        usernames = await self.read_users(location)

        if username.lower() in usernames:
            return True
        else:
            return False

    async def read_users(self, location, max_count):
        url = location['params']['location']

        with urlopen(url) as response:
            content_bytes = response.read()
            try:
                content = content_bytes.decode('utf-8')
            except Exception:
                content = content_bytes.decode('latin-1')

        usernames = [
            re.sub('^@', '', line.strip().lower())
            for line in content.splitlines()
            if line.strip() != '' and not line.strip().startswith('#')
        ]

        if max_count is None:
            return usernames
        else:
            return usernames[0:max_count]

    def parse_params(self, args, check_missing=True):
        return Params.parse_params(args, self.params, check_missing)


