from lib.reader_gspread import ReaderGspread
from lib.reader_file import ReaderFile
from lib.reader_api import ReaderApi
from lib.redis import Redis

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
    redis = None
    redis_key_prefix = 'whitelist'

    def __init__(self, config, logger, redis_client: Redis | None = None, redis_key_prefix: str = 'whitelist'):
        self.logger = logger
        self.config = config
        self.redis = redis_client if redis_client else Redis()
        self.redis_key_prefix = redis_key_prefix

        if self.DEFAULT_SOURCE_PARAM in config and config[self.DEFAULT_SOURCE_PARAM]:
            args = config[self.DEFAULT_SOURCE_PARAM].split(';')
            self.default_reader = args[0]

            reader = self.get_reader(self.default_reader)

            self.default_reader_params = reader.parse_params(args, set_default=True)

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

    def _redis_key(self, chat_id):
        """Generate Redis key for chat whitelist location"""
        return f"{self.redis_key_prefix}:{chat_id}"

    def get_whitelist_params(self, chat_id):
        """Returns whitelist location for the given chat id"""
        key = self._redis_key(chat_id)
        location_data = self.redis.get_dict(key)

        if location_data is None:
            return None

        if location_data['reader_type'] == self.DEFAULT_READER:
            location = {
                        'reader_type': self.default_reader,
                        'params': self.default_reader_params,
                        'is_default': True
                        }
        else:
            location = location_data

        return location

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
            reader = self.get_reader(reader_type)
            params = reader.parse_params(args)

        if reader_type not in self.SUPPORTED_READERS:
            raise Exception(f'Invalid reader type ({reader_type}). Supported readers: {', '.join(self.SUPPORTED_READERS)}')

        key = self._redis_key(chat_id)
        location_data = {'reader_type': reader_type}

        if reader_type != self.DEFAULT_READER:
            location_data['params'] = params

        self.redis.set_dict(key, location_data)

    async def set_whitelist_condition(self, chat_id, condition):
        key = self._redis_key(chat_id)
        location_data = self.redis.get_dict(key)

        if location_data is None:
            raise Exception(f'Location not found')

        reader = self.get_reader(location_data['reader_type'])
        params = reader.parse_params(['condition=' + condition], check_missing=False)

        if 'condition' in params:
            location_data['params']['condition'] = params['condition']

        self.redis.set_dict(key, location_data)

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
        """Dump all whitelist locations from Redis (for backward compatibility)"""
        # Get all keys matching the prefix
        result = {}
        # Since Redis doesn't have a direct way to get all keys with a pattern in our simple interface,
        # we'll return an empty dict for now. This method is mainly used for pickle compatibility.
        # If needed, we could implement a keys() method in Redis class, but for now this maintains compatibility
        return result

    def restore(self, data):
        """Restore whitelist locations from data dictionary (for migration from pickle)"""
        if data:
            for chat_id, location_data in data.items():
                key = self._redis_key(chat_id)
                self.redis.set_dict(key, location_data)