import logging


class StandardFormatter(logging.Formatter):
    log_format = "[%(asctime)s] (%(levelname)s) %(message)s"

    def get_format(self, record):
        return self.log_format

    def format(self, record):
        formatter = logging.Formatter(self.get_format(record), datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)
