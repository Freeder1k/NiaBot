import discord
from discord import Permissions, Embed

import handlers.logging
from handlers.commands import command, hybridCommand
from handlers.commands.commandEvent import CommandEvent
from wrappers import botConfig


class GuildQuestionnaire(discord.ui.Modal, title='Nerfuria Guild Application'):
    name = discord.ui.TextInput(label='Minecraft IGN:', max_length=16)
    guilds = discord.ui.TextInput(
        label='Previous guilds and why you left:',
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=1000
    )
    other = discord.ui.TextInput(
        label='Anything else you would like to add:',
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=1000
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'Your application has been submitted!', ephemeral=True)


async def _guildQuestionnaireCallback(interaction: discord.Interaction):
    try:
        await interaction.response.send_modal(GuildQuestionnaire())
    except Exception as e:
        await handlers.logging.error(exc_info=e)


class ApplyCommand(hybridCommand.HybridCommand):
    def __init__(self):
        super().__init__(
            name="apply",
            aliases=(),
            params=[],
            description="Send application message.",
            base_perms=Permissions().none(),
            permission_lvl=command.PermissionLevel.CHIEF
        )

    async def _execute(self, event: CommandEvent):
        embed = Embed(
            title="Application",
            description="Interested in joining the guild? Fill out the application form by clicking apply below!",
            color=botConfig.DEFAULT_COLOR
        )

        view = discord.ui.View(timeout=None)
        button = discord.ui.Button(
            label="Apply",
            style=discord.ButtonStyle.green,
        )
        view.add_item(button)
        button.callback = _guildQuestionnaireCallback
        await event.channel.send(embed=embed, view=view)
