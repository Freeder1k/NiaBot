import logging

import common.utils.logutils.standardFormatter


class ColoredFormatter(common.utils.logutils.standardFormatter.StandardFormatter):
    grey = "\x1b[30;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    def __init__(self):
        super().__init__()
        self.FORMATS = {
            logging.DEBUG: self.grey + super().log_format + self.reset,
            logging.INFO: self.reset + super().log_format + self.reset,
            logging.WARNING: self.yellow + super().log_format + self.reset,
            logging.ERROR: self.red + super().log_format + self.reset,
            logging.CRITICAL: self.bold_red + super().log_format + self.reset
        }

    def get_format(self, record):
        return self.FORMATS.get(record.levelno)
