import gspread
import re
import os
from lib.params import Params

"""
Google Spreadsheets Datasource: checks telegram login against given column on given sheet of online table
"""

class ReaderGspread:
    reader = None
    config = {}
    sources = {}

    params = {
                'location': {'type': str},
                'column': {'default': 1, 'type': int},
                'sheet': {'default': 1, 'type': int},
                'condition': {'default': None, 'type': 'condition'}
             }

    def __init__(self, config):
        if config:
            self.config = config

        if 'gsa_file' not in config:
            raise Exception('No google service account file given for gspread reader')
        elif not os.path.exists(config['gsa_file']):
            raise Exception(f'Google service account file not found: {config['gsa_file']}')

        self.reader = gspread.service_account(filename=config['gsa_file'])

    async def check_allowed_user(self, location, username):
        usernames = await self.read_users(location)

        if 'condition' in location['params']:
            cond_values = await self.read_cond_column(location)
        else:
            cond_values = None

        for i, list_username in enumerate(usernames):
            list_username = re.sub('^@', '', list_username.lower().strip())
            if username == list_username:
                if cond_values is None:
                    return True
                elif Params.check_condition(location['params']['condition'], cond_values[i], lower_case=True):
                    return True
                else:
                    return False

        if username.lower() in map(lambda x: re.sub('^@', '', x.lower().strip()), usernames):
            return True
        else:
            return False

    async def read_users(self, location, max_count = None):
        """Load users"""
        if location['params']['location'] not in self.sources:
            spreadsheet = self.reader.open_by_url(location['params']['location'])
            self.sources[location['params']['location']] = spreadsheet.get_worksheet(location['params']['sheet'] - 1)

        usernames = self.sources[location['params']['location']].col_values(location['params']['column'])

        if max_count is None:
            return usernames
        else:
            return usernames[0:max_count]

    async def read_cond_column(self, location):
        """ Load condition column values """
        if location['params']['location'] not in self.sources:
            spreadsheet = self.reader.open_by_url(location['params']['location'])
            self.sources[location['params']['location']] = spreadsheet.get_worksheet(location['params']['sheet'] - 1)

        cond_column = self.sources[location['params']['location']].col_values(int(location['params']['condition']['param']))

        return cond_column

    def parse_params(self, args, check_missing=True, set_default=False):
        """
        Parse named parameters from args array in format parameter_name=parameter_value
        Uses self.params to determine supported parameters and their types
        """
        return Params.parse_params(args, self.params, check_missing, set_default)