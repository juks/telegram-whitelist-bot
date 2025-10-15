import gspread
import re
import os

"""
Google Spreadsheets Datasource: checks telegram login against given column on given sheet of online table
"""

class ReaderGspread:
    reader = None
    config = {}
    sources = {}

    def __init__(self, config):
        if config:
            self.config = config

        if 'gsa_file' not in config:
            raise Exception('No google service account file given for gspread reader')
        elif not os.path.exists(config['gsa_file']):
            raise Exception(f'Google service account file not found: {config['gsa_file']}')

        self.reader = gspread.service_account(filename=config['gsa_file'])

    async def check_allowed_user(self, location, username):
        """Load locations"""
        if location['params']['location'] not in self.sources:
            spreadsheet = self.reader.open_by_url(location['params']['location'])

            self.sources[location['params']['location']] = spreadsheet.get_worksheet(location['params']['sheet'])

        usernames = self.sources[location['params']['location']].col_values(location['params']['column'])

        if username.lower() in map(lambda x: re.sub('^@', '', x.lower().strip()), usernames):
            return True
        else:
            return False


    def parse_params(self, args):
        params = {}

        # <reader type> <whilelist location> [column=1] [sheet=0]
        for i, p in enumerate([
            {'name': 'location', 'type': str},
            {'name': 'column', 'default': 1, 'type': int},
            {'name': 'sheet', 'default': 0, 'type': int}
        ]):
            if len(args) > 1 + i:
                if p['type'] is int:
                    params[p['name']] = int(args[1 + i])
                else:
                    params[p['name']] = args[1 + i]
            elif 'default' in p:
                params[p['name']] = p['default']

        return params