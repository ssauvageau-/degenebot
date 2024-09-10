from datetime import datetime, timedelta, timezone
import json
import logging
import os
from typing import Dict

import discord
from discord import app_commands, TextStyle
from discord.ext import commands

COMMAND_ROLE_ALLOW_LIST = ["Actual Admin"]


@app_commands.guild_only()
class ModerationCommandGroup(app_commands.Group, name="moderation"):
    def __init__(self, bot: commands.Bot):
        self.logger = logging.getLogger("bot")
        self.log_channel_name = "degen-log"
        self.bot = bot
        self.archive_cat = 1242564359712935977
        super().__init__()

    @app_commands.command(
        name="clear-messages",
        description="Delete a number of recent messages in the channel",
    )
    @app_commands.describe(number="The number of recent messages to delete.")
    @app_commands.checks.has_any_role(*COMMAND_ROLE_ALLOW_LIST)
    async def clear(self, interaction: discord.Interaction, number: int):
        await interaction.response.defer(ephemeral=True, thinking=True)

        if number > 5:
            deletions = [5 for _ in range(0, int(number / 5))]
            if number % 5 > 0:
                deletions.append(number % 5)
        else:
            deletions = [number]

        for deletion in deletions:
            async for message in interaction.channel.history(limit=deletion):
                await message.delete()

        await interaction.followup.send(f"Deleted {number} messages", ephemeral=True)

    @app_commands.command(
        name="move_channel",
        description="Moves a channel into the specified Category. Does not touch permissions.",
    )
    @app_commands.describe(
        channel_name="The channel to move. Case-sensitive.",
        category_name="The category to move the channel to. Case-sensitive.",
    )
    @app_commands.checks.has_any_role(*COMMAND_ROLE_ALLOW_LIST)
    async def move_channel(
        self, interaction: discord.Interaction, channel_name: str, category_name: str
    ):
        await interaction.response.defer(ephemeral=True, thinking=True)

        channel = ""
        cat = ""

        for ch in interaction.guild.channels:
            if ch.name == channel_name:
                channel = ch
            elif ch.name == category_name:
                cat = ch
        if not channel:
            await interaction.followup.send(
                f"Could not identify channel with name: {channel_name}."
            )
            return
        if not cat:
            await interaction.followup.send(
                f"Could not identify channel with name: {category_name}."
            )
            return
        await channel.edit(category=cat)
        await interaction.followup.send(
            f"Successfully moved {channel_name} to {category_name}."
        )

    def get_user_perms(
        self, guild: discord.Interaction.guild, user: discord.User
    ) -> str:
        roles = []
        mem = ""
        for role in guild.roles:
            for member in role.members:
                if user.id == member.id:
                    roles.append(role.name)
                    mem = member
        channels = []
        for channel in guild.channels:
            channels.append(f"{channel.name}: {channel.permissions_for(mem).value:b}")
        newline = "\n\t"
        ret = f"User has Roles:\n\t{newline.join(roles)}\n\nUser has channel overrides:\n\t{newline.join(channels)}"
        return ret

    @app_commands.command(
        name="user_perms",
        description="Get the roles and channel permission overrides of a user.",
    )
    @app_commands.checks.has_any_role(*COMMAND_ROLE_ALLOW_LIST)
    async def user_perms(self, interaction: discord.Interaction, user: discord.User):
        await interaction.response.send_message(
            self.get_user_perms(interaction.guild, user), ephemeral=True
        )
