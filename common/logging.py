import logging
import os
from configparser import ConfigParser
from typing import Final

from discord import Client

import common.utils.logutils.discordHandler
from common.utils.logutils.coloredFormatter import ColoredFormatter
from common.utils.logutils.standardFormatter import StandardFormatter

_config = ConfigParser()
if os.path.exists('logger_config.ini'):
    _config.read('logger_config.ini')
else:
    _config.add_section('LOGGING')
    _config.set('LOGGING', 'LOG_FILE', 'bot.log')
    _config.set('LOGGING', 'ENABLE_DEBUG', 'True')
    _config.set('LOGGING', 'LOG_CHANNEL', '0')

LOG_FILE: Final = _config.get('LOGGING', 'LOG_FILE')
ENABLE_DEBUG: Final = _config.getboolean('LOGGING', 'ENABLE_DEBUG')
LOG_CHANNEL: Final = _config.getint('LOGGING', 'LOG_CHANNEL')

_logger = logging.getLogger('NiaBot')
log_lvl = logging.DEBUG if ENABLE_DEBUG else logging.INFO
_logger.setLevel(log_lvl)


def debug(*args):
    """
    Logs the args at debug level
    """
    _logger.debug(msg=' '.join((str(arg) for arg in args)))


def info(*args):
    """
    Logs the args at info level
    """
    _logger.info(msg=' '.join((str(arg) for arg in args)))


def warning(*args):
    """
    Logs the args at warning level
    """
    _logger.warning(msg=' '.join((str(arg) for arg in args)))


def error(*args, exc_info=None, extra=None):
    """
    Logs the args at error level

    :param exc_info: Additional exception info to log
    :param extra: Mapping of extra objects to log
    """
    _logger.error(msg=' '.join((str(arg) for arg in args)), exc_info=exc_info, extra=extra)


def _init_base_handlers():
    console = logging.StreamHandler()
    console.setFormatter(ColoredFormatter())

    _logger.addHandler(console)

    try:
        logfile_handler = logging.FileHandler(LOG_FILE)
        logfile_handler.setFormatter(StandardFormatter())

        _logger.addHandler(logfile_handler)
    except Exception as e:
        error("Failed to initialize file logger handler:", e)


_init_base_handlers()


async def init_discord_handler(client: Client):
    """
    Initializes the discord logger handler
    """
    try:
        channel = await client.fetch_channel(LOG_CHANNEL)

        if not channel.permissions_for(channel.guild.me).send_messages:
            warning("Insufficient permissions to send messages to discord log channel.")
            return

        discord_handler = common.utils.logutils.discordHandler.DiscordHandler(client, LOG_CHANNEL)
        discord_handler.setFormatter(ColoredFormatter())

        _logger.addHandler(discord_handler)
    except Exception as e:
        error("Failed to initialize discord logger handler:", exc_info=e)
