import ast
import os.path
from configparser import ConfigParser
from typing import Final

config = ConfigParser()

if os.path.exists('bot_config.ini'):
    config.read('bot_config.ini')
else:
    config.add_section('MAIN')
    config.set('MAIN', 'PREFIX', '.')
    config.set('MAIN', 'DEV_USER_IDS', '[]')

    config.add_section('GUILD')
    config.set('GUILD', 'GUILD_NAME', 'Nerfuria')
    config.set('GUILD', 'GUILD_DISCORD', '0')

    config.add_section('COLORS')
    config.set('COLORS', 'DEFAULT_COLOR', '3603854')
    config.set('COLORS', 'SUCCESS_COLOR', '7844437')
    config.set('COLORS', 'ERROR_COLOR', '14495300')
    config.set('COLORS', 'INFO_COLOR', '3901635')

    config.add_section('LOGGING')
    config.set('LOGGING', 'LOG_FILE', 'nia-bot.log')
    config.set('LOGGING', 'ENABLE_DEBUG', 'True')

    with open('bot_config.ini', 'w') as f:
        config.write(f)

PREFIX: Final = config.get('MAIN', 'PREFIX')
DEV_USER_IDS: Final = ast.literal_eval(config.get('MAIN', 'DEV_USER_IDS'))

GUILD_NAME: Final = config.get('GUILD', 'GUILD_NAME')
GUILD_DISCORD: Final = config.getint('GUILD', 'GUILD_DISCORD')

# EMBED COLORS
DEFAULT_COLOR: Final = config.getint('COLORS', 'DEFAULT_COLOR')
SUCCESS_COLOR: Final = config.getint('COLORS', 'SUCCESS_COLOR')
ERROR_COLOR: Final = config.getint('COLORS', 'ERROR_COLOR')
INFO_COLOR: Final = config.getint('COLORS', 'INFO_COLOR')

# LOGGING
LOG_FILE: Final = config.get('LOGGING', 'LOG_FILE')
ENABLE_DEBUG: Final = config.getboolean('LOGGING', 'ENABLE_DEBUG')
