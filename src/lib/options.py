"""
Simple options class
"""

class Options():
    storage = {}
    valid_options = {}
    valid_types = ['bool', 'int', 'str']
    valid_options = {}

    def __init__(self, setup):
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


    def get_option(self, chat_id, option_name):
        if option_name not in self.valid_options:
            raise Exception(f'Unknown option name: {option_name}')

        if chat_id in self.storage and option_name in self.storage[chat_id]:
            return self.storage[chat_id][option_name]
        elif option_name in self.valid_options and 'default' in self.valid_options[option_name]:
            return self.valid_options[option_name]['default']
        else:
            match self.valid_options[option_name]['type']:
                case 'bool':
                    return False
                case 'int':
                    return 0
                case 'str':
                    return ''

    def set_option(self, chat_id, option_name, option_value):
        if option_name not in self.valid_options:
            raise Exception(f'Unknown option {option_name}')

        if chat_id not in self.storage:
            self.storage[chat_id] = {}

        match self.valid_options[option_name]['type']:
            case 'bool':
                self.storage[chat_id][option_name] = bool(option_value)
            case 'int':
                self.storage[chat_id][option_name] = int(option_value)
            case 'str':
                self.storage[chat_id][option_name] = str(option_value)

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
        return self.storage

    def restore(self, data):
        self.storage = data