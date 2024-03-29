from datetime import datetime, timedelta, timezone
import json
import logging
import os
from typing import Dict

import discord
from discord import app_commands, TextStyle
from discord.ext import commands

COMMAND_ROLE_ALLOW_LIST = ["Skar"]


@app_commands.guild_only()
class ModerationCommandGroup(app_commands.Group, name="moderation"):
    def __init__(self, bot: commands.Bot):
        self.logger = logging.getLogger("bot")
        self.log_channel_name = "degen-log"
        self.bot = bot
        super().__init__()

    @app_commands.command(
        name="clear-messages",
        description="Delete a number of recent messages in the channel",
    )
    @app_commands.describe(number="The number of recent messages to delete")
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
