from lib.reader_gspread import ReaderGspread
from lib.reader_file import ReaderFile
from lib.reader_api import ReaderApi

class Whitelist:
    DEFAULT_SOURCE_PARAM = 'default_source'
    DEFAULT_READER = 'default'
    READER_GSPREAD = 'gspread'
    READER_FILE = 'file'
    READER_API = 'api'
    SUPPORTED_READERS = [DEFAULT_READER, READER_GSPREAD, READER_FILE, READER_API]

    default_reader = None
    default_reader_params = None
    default_source = None
    config = None

    readers = {}
    chats = {}
    locations = {}

    def __init__(self, config, logger):
        self.logger = logger
        self.config = config

        if self.DEFAULT_SOURCE_PARAM in config and config[self.DEFAULT_SOURCE_PARAM]:
            args = config[self.DEFAULT_SOURCE_PARAM].split(',')
            self.default_reader = args[0]
            self.default_reader_params = self.parse_reader_params(self.default_reader, args)

    def get_reader(self, reader_type):
        """Returns whitelist reader of given type"""
        if reader_type not in self.SUPPORTED_READERS:
            raise Exception('Invalid whitelist type')

        if reader_type == self.DEFAULT_READER:
            reader_type = self.default_reader

        if reader_type not in self.readers:
            match reader_type:
                case self.READER_GSPREAD:
                    self.readers[reader_type] = ReaderGspread(self.config)
                case self.READER_FILE:
                    self.readers[reader_type] = ReaderFile(self.config)
                case self.READER_API:
                    self.readers[reader_type] = ReaderApi(self.config)

        return self.readers[reader_type]

    def get_whitelist_params(self, chat_id):
        """Returns whitelist location for the given chat id"""
        if chat_id not in self.locations:
            return None
        else:
            location = self.locations[chat_id]

            if location['reader_type'] == self.DEFAULT_READER:
                location = {
                            'reader_type': self.default_reader,
                            'params': self.default_reader_params,
                            'is_default': True
                            }

            return location

    async def test(self, chat_id):
        """Get the result of whitelist test: 3 entries or check if user bob can access api"""
        location = self.get_whitelist_params(chat_id)

        if location is None:
            raise Exception('No whitelist for this chat')

        reader = self.get_reader(location['reader_type'])

        if not reader:
            raise Exception('Unsupported reader type')

        # If class supports getting the list of users
        if hasattr(reader, 'read_users'):
            entries = await reader.read_users(location, 3)
            entries = list(map(lambda x: x[0:3] + '...', entries))
            
            return entries
        # If class only checks single user
        elif isinstance(reader, ReaderApi):
            username = 'bob'

            try:
                result = await reader.check_allowed_user(location, username)
            except Exception as e:
                return f'user {username} is not allowed: {str(e)}'

            if not result:
                return f'user {username} is not allowed'
            else:
                return f'user {username} is allowed'
        else:
            return ['n/a']

    def set_whitelist_params(self, chat_id, args):
        """Sets whitelist location for the given chat id"""
        if len(args) < 1:
            raise Exception('Please provide whitelist type')

        reader_type = args[0]

        if reader_type == self.DEFAULT_READER:
            if self.default_reader_params is None:
                raise Exception('Default reader is not initialized')

            params = self.default_reader_params
        else:
            if len(args) < 1:
                raise Exception('Please provide whitelist location')

            params = self.parse_reader_params(reader_type, args)

        if reader_type not in self.SUPPORTED_READERS:
            raise Exception(f'Invalid reader type ({reader_type}). Supported readers: {', '.join(self.SUPPORTED_READERS)}')

        self.locations[chat_id] = {'reader_type': reader_type}

        if reader_type != self.DEFAULT_READER:
            self.locations[chat_id]['params'] = params

    def parse_reader_params(self, reader_type, args):
        """Parses args array to set reader parameters"""
        reader = self.get_reader(reader_type)

        return reader.parse_params(args)

    async def check_allowed_user(self, chat_id, username):
        """Checks if user is allowed to join to the given group"""
        location = self.get_whitelist_params(chat_id)

        if location is None:
            raise Exception('No whitelist for this chat')

        reader = self.get_reader(location['reader_type'])

        if not reader:
            raise Exception('Unsupported reader type')

        return await reader.check_allowed_user(location, username)

    def dump(self):
        return self.locations

    def restore(self, data):
        self.locations = data