import pickle
import threading

"""
Simple permanent storage class
"""

class Permanent():
    file_name = None
    lock = threading.Lock()
    storage = {}
    logger = None

    def __init__(self, file_name, logger):
        self.file_name = file_name
        self.logger = logger

    def store(self, option_name, data):
        self.storage[option_name] = data

        if self.file_name:
            with self.lock:
                try:
                    with open(self.file_name, 'wb') as f:
                        pickle.dump(self.storage, f)
                except FileNotFoundError:
                    self.logger.info("File not found: %s", self.file_name)
        else:
            self.logger.info(f'No pickle file, won\'t dump {option_name}')

    def restore(self, option_name = None):
        if self.file_name:
            with self.lock:
                try:
                    with open(self.file_name, 'rb') as f:
                        self.storage = pickle.load(f)

                        if option_name:
                            if option_name in self.storage:
                                return self.storage[option_name]
                            else:
                                return None
                        else:
                            return self.storage
                except FileNotFoundError:
                    self.logger.error("File not found: %s", self.file_name)
        else:
            self.logger.info(f'No pickle file, won\'t load {option_name}')
