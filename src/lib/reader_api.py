import json
import re
from lib.params import Params
from urllib.parse import urlencode
from urllib.request import Request, urlopen

"""
REST API Datasource: checks a single telegram login against a remote HTTP endpoint.
Supports Bearer token auth via per-source params or a default token from config.

Endpoint URL handling:
- If the configured URL contains "{username}", it will be replaced with the checked username.
- Otherwise, the username will be appended as a query string parameter "username".

Expected response formats indicating access granted:
- JSON boolean true
- JSON object with truthy flag: one of keys ["allowed", "allow", "ok", "in_whitelist"]
- Plain text "true" / "1" (case-insensitive)
"""


class ReaderApi:
    config = {}

    params = {'location': {'type': str}, 'token': {'type': str}}

    def __init__(self, config):
        if config:
            self.config = config

    async def check_allowed_user(self, location, username):
        base_url = location['params']['location']

        # Build request URL
        if '{username}' in base_url:
            url = base_url.replace('{username}', re.sub('^@', '', username))
        else:
            sep = '&' if '?' in base_url else '?'
            url = f"{base_url}{sep}{urlencode({'username': re.sub('^@', '', username)})}"

        # Resolve token
        token = None
        if 'token' in location['params'] and location['params']['token']:
            token = location['params']['token']
        elif 'api_token' in self.config and self.config['api_token']:
            token = self.config['api_token']

        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'

        request = Request(url, headers=headers)
        with urlopen(request) as response:
            content_bytes = response.read()

        # Try JSON boolean or object flags
        try:
            data = json.loads(content_bytes.decode('utf-8'))
            if isinstance(data, bool):
                return bool(data)
            if isinstance(data, dict):
                for key in ['result', 'allowed', 'allow', 'ok', 'in_whitelist']:
                    if key in data:
                        return bool(data[key])
        except Exception:
            pass

        # Fallback to plain text
        try:
            content = content_bytes.decode('utf-8').strip().lower()
        except Exception:
            content = content_bytes.decode('latin-1').strip().lower()

        return content in ['true', '1', 'yes', 'ok']

    def parse_params(self, args, check_missing=True):
        """Parse named parameters from args array in format parameter_name=parameter_value
        Uses self.params to determine supported parameters and their types
        """
        return Params.parse_params(args, self.params, check_missing)


