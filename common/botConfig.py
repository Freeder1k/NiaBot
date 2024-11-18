import ast
import os.path
from configparser import ConfigParser
from typing import Final


class BotConfig:
    def __init__(self, path: str):
        self.path = path
        config = ConfigParser()

        if os.path.exists(self.path):
            config.read(self.path)
        else:
            config.add_section('MAIN')
            config.set('MAIN', 'PREFIX', '.')
            config.set('MAIN', 'DEV_USER_IDS', '[]')
            config.set('MAIN', 'BOT_NAME', '')

            config.add_section('GUILD')
            config.set('GUILD', 'GUILD_NAME', 'Nerfuria')
            config.set('GUILD', 'GUILD_DISCORD', '0')

            config.add_section('COLORS')
            config.set('COLORS', 'DEFAULT_COLOR', '3603854')
            config.set('COLORS', 'SUCCESS_COLOR', '7844437')
            config.set('COLORS', 'ERROR_COLOR', '14495300')
            config.set('COLORS', 'INFO_COLOR', '3901635')

            with open(self.path, 'w') as f:
                config.write(f)

        # MAIN
        self.PREFIX: Final = config.get('MAIN', 'PREFIX')
        self.DEV_USER_IDS: Final[list[str]] = ast.literal_eval(config.get('MAIN', 'DEV_USER_IDS'))
        self.BOT_NAME: Final = config.get('MAIN', 'BOT_NAME')

        # GUILD
        self.GUILD_NAME: Final = config.get('GUILD', 'GUILD_NAME')
        self.GUILD_DISCORD: Final = config.getint('GUILD', 'GUILD_DISCORD')

        # EMBED COLORS
        self.DEFAULT_COLOR: Final = config.getint('COLORS', 'DEFAULT_COLOR')
        self.SUCCESS_COLOR: Final = config.getint('COLORS', 'SUCCESS_COLOR')
        self.ERROR_COLOR: Final = config.getint('COLORS', 'ERROR_COLOR')
        self.INFO_COLOR: Final = config.getint('COLORS', 'INFO_COLOR')
