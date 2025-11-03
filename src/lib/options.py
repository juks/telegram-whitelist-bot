"""
Simple options class backed by Redis storage
"""
from lib.redis import Redis


class Options():
    storage = {}
    valid_options = {}
    valid_types = ['bool', 'int', 'str']
    valid_options = {}
    redis = None
    redis_key_prefix = 'options'

    def __init__(self, setup, redis_client: Redis | None = None, redis_key_prefix: str = 'options'):
        self.redis = redis_client if redis_client else Redis()
        self.redis_key_prefix = redis_key_prefix

        for option_name in setup:
            if 'type' not in setup[option_name] or setup[option_name]['type'] not in self.valid_types:
                raise Exception('Invalid option type')

            match setup[option_name]['type']:
                case 'bool':
                    self.valid_options[option_name] = {'type': 'bool'}
                case 'int':
                    self.valid_options[option_name] = {'type': 'int'}
                case 'str':
                    self.valid_options[option_name] = {'type': 'str'}
                case _:
                    raise Exception('Invalid option type')

            if 'default' in setup[option_name]:
                self.valid_options[option_name]['default'] = setup[option_name]['default']

            if 'description' in setup[option_name]:
                self.valid_options[option_name]['description'] = setup[option_name]['description']

    def _redis_key(self, chat_id, option_name):
        return f"{self.redis_key_prefix}:{chat_id}:{option_name}"

    def get_option(self, chat_id, option_name):
        if option_name not in self.valid_options:
            raise Exception(f'Unknown option name: {option_name}')

        key = self._redis_key(chat_id, option_name)
        raw_value = self.redis.get(key)

        if raw_value is None:
            if option_name in self.valid_options and 'default' in self.valid_options[option_name]:
                return self.valid_options[option_name]['default']
            else:
                match self.valid_options[option_name]['type']:
                    case 'bool':
                        return False
                    case 'int':
                        return 0
                    case 'str':
                        return ''

        match self.valid_options[option_name]['type']:
            case 'bool':
                return str(raw_value).lower() in ['1', 'true', 'yes', 'on']
            case 'int':
                return int(raw_value)
            case 'str':
                return str(raw_value)

    def set_option(self, chat_id, option_name, option_value):
        if option_name not in self.valid_options:
            raise Exception(f'Unknown option {option_name}')

        key = self._redis_key(chat_id, option_name)

        match self.valid_options[option_name]['type']:
            case 'bool':
                value = '1' if bool(option_value) else '0'
            case 'int':
                value = str(int(option_value))
            case 'str':
                value = str(option_value)

        self.redis.set(key, value)

    def get_reference(self):
        result = ''

        for option_name in self.valid_options:
            result += f'• <b>{option_name}</b> ({self.valid_options[option_name]['type']})'
            if 'default' in self.valid_options[option_name]:
                result += ' default <b>' + str(self.valid_options[option_name]['default']) + '</b>'

            if 'description' in self.valid_options[option_name]:
                result += ': ' + self.valid_options[option_name]['description']

            result += '\n'

        return result

    def dump(self):
        # Kept for backward compatibility (no-op with Redis backend)
        return {}

    def restore(self, data):
        # Kept for backward compatibility (no-op with Redis backend)
        return None