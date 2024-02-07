import logging

from discord import Client

import utils.logutils.discordHandler
from utils.logutils.coloredFormatter import ColoredFormatter
from utils.logutils.standardFormatter import StandardFormatter
from wrappers import botConfig

_logger = logging.getLogger('NiaBot')
log_lvl = logging.DEBUG if botConfig.ENABLE_DEBUG else logging.INFO
_logger.setLevel(log_lvl)


def debug(*args):
    _logger.debug(msg=' '.join((str(arg) for arg in args)))


def info(*args):
    _logger.info(msg=' '.join((str(arg) for arg in args)))


def warning(*args):
    _logger.warning(msg=' '.join((str(arg) for arg in args)))


def error(*args, exc_info=None, extra=None):
    _logger.error(msg=' '.join((str(arg) for arg in args)), exc_info=exc_info, extra=extra)


def _init_base_handlers():
    console = logging.StreamHandler()
    console.setFormatter(ColoredFormatter())

    _logger.addHandler(console)

    try:
        logfile_handler = logging.FileHandler(botConfig.LOG_FILE)
        logfile_handler.setFormatter(StandardFormatter())

        _logger.addHandler(logfile_handler)
    except Exception as e:
        error("Failed to initialize file logger handler:", e)


_init_base_handlers()


async def init_discord_handler(client: Client):
    try:
        channel_id = botConfig.LOG_CHANNEL
        channel = await client.fetch_channel(channel_id)

        if not channel.permissions_for(channel.guild.me).send_messages:
            warning("Insufficient permissions to send messages to discord log channel.")
            return

        discord_handler = utils.logutils.discordHandler.DiscordHandler(client, channel_id)
        discord_handler.setFormatter(ColoredFormatter())

        _logger.addHandler(discord_handler)
    except Exception as e:
        error("Failed to initialize discord logger handler:", exc_info=e)
