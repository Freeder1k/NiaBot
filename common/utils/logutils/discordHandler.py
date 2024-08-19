import logging

from discord import Client, Embed

import common.utils.misc
from common import botConfig


class DiscordHandler(logging.Handler):
    def __init__(self, client: Client, channel_id):
        super().__init__()

        self._client = client
        self._channel_id = channel_id

    def emit(self, record):
        if not self._client.is_closed():
            self._client.loop.create_task(self._send(record))

    async def _send(self, record):
        try:
            channel = self._client.get_channel(self._channel_id)

            msg = self.format(record)
            splits = [f"```ansi\n{s}```" for s in common.utils.misc.split_str(msg, 1950, '\n')]

            if botConfig.DEV_USER_IDS and record.levelno >= logging.ERROR:
                await channel.send(''.join(f"<@{uid}>" for uid in botConfig.DEV_USER_IDS))
            for split in splits:
                await channel.send(split)

            if hasattr(record, 'command_event'):
                event = record.command_event
                embed = Embed(
                    color=botConfig.ERROR_COLOR,
                    title=f"Further Exception Information:",
                    description=f"Server: ``{event.guild}``\n"
                                f"Channel: ``#{event.channel.name}``\n"
                                f"Message link: {event.message.jump_url}"
                )
                embed.add_field(name="Command Event:", value=f"```\n{event}```", inline=False)
                await channel.send(embed=embed)
        except Exception as e:
            print(f"Failed to send log message to Discord: {e}")
