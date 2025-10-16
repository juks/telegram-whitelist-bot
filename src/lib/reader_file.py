import re
from urllib.request import urlopen

"""
Text File Datasource: checks telegram login against a plain text file available by URL.
Each line should contain one username (with or without leading '@').
"""

class ReaderFile:
    config = {}

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

    def parse_params(self, args):
        params = {}

        # <reader type> <whilelist location>
        for i, p in enumerate([
            {'name': 'location', 'type': str},
        ]):
            if len(args) > 1 + i:
                if p['type'] is int:
                    params[p['name']] = int(args[1 + i])
                else:
                    params[p['name']] = args[1 + i]
            elif 'default' in p:
                params[p['name']] = p['default']

        return params


