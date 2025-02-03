from datetime import datetime, timedelta, timezone
import json
import logging
import os
import asyncio
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

    @app_commands.command(
        name="user_perms",
        description="Get the roles and channel permission overrides of a user.",
    )
    @app_commands.checks.has_any_role(*COMMAND_ROLE_ALLOW_LIST)
    async def get_user_perms(
        self, interaction: discord.Interaction, user: discord.User
    ):
        roles = []
        mem = ""
        for role in interaction.guild.roles:
            if "everyone" in role.name:
                continue
            for member in role.members:
                if user.id == member.id:
                    roles.append(role.name)
                    mem = member
        channels = []
        for channel in interaction.guild.channels:
            channels.append(f"{channel.name}: {channel.permissions_for(mem).value:b}")
        newline = "\n\t"
        ret = f"User has Roles:\n\t{newline.join(roles)}\n\nUser has channel overrides:\n\t{newline.join(channels)}"
        if len(ret) < 2000:
            await interaction.response.send_message(ret, ephemeral=True)
        else:
            fn = "out.txt"
            with open(fn, "w") as f:
                f.write(ret)
            await interaction.response.send_message(
                file=discord.File(fn), ephemeral=True
            )
            os.unlink(fn)

    @app_commands.command(
        name="range-delete",
        description="Delete all messages in a channel that occur between two supplied messages, inclusive.",
    )
    @app_commands.describe(
        msg_one="ID of the first of the two message block limits, inclusive.",
        msg_two="ID of the second of the two message block limits, inclusive.",
    )
    @app_commands.checks.has_any_role(*COMMAND_ROLE_ALLOW_LIST)
    async def range_delete(
        self,
        interaction: discord.Interaction,
        msg_one: str,
        msg_two: str,
        limit: int = 200,
    ):
        chan = interaction.channel
        m1 = await chan.fetch_message(int(msg_one))
        m2 = await chan.fetch_message(int(msg_two))
        if m1 is None or m2 is None:
            await interaction.response.send_message(
                "Messages not found in calling channel, terminating operation.\nYou must use this command from the channel that contains both messages.",
                ephemeral=True,
            )
        await interaction.response.defer(ephemeral=True, thinking=True)
        hist = [message async for message in chan.history(limit=limit)]
        print(hist)
        bound1, bound2 = 0, 0
        for x in range(len(hist)):
            if hist[x].id == int(msg_one):
                bound1 = x
            elif hist[x].id == int(msg_two):
                bound2 = x
        if bound1 == 0 or bound2 == 0:
            await interaction.followup.send(
                f"Messages not found within history of {limit} messages in channel.",
                ephemeral=True,
            )
        # python list slicing is [x:y) by default, need to add 1 to upper bound
        deletions = (
            hist[bound1 : bound2 + 1] if bound1 < bound2 else hist[bound2 : bound1 + 1]
        )
        queue = [deletions[i : i + 5] for i in range(0, len(deletions), 5)]
        for batch in queue:
            for msg in batch:
                await msg.delete()
            await asyncio.sleep(1)
        await interaction.followup.send(
            f"Deleted {len(deletions)} messages.", ephemeral=True
        )

    @app_commands.command(
        name="get-channel-pos",
        description="The position in the channel list. This is a number that starts at 0.",
    )
    @app_commands.checks.has_any_role(*COMMAND_ROLE_ALLOW_LIST)
    async def get_channel_position(
        self, interaction: discord.Interaction, channel: discord.TextChannel
    ):
        await interaction.response.send_message(
            f"{channel.jump_url} is in position {channel.position}", ephemeral=True
        )

    @app_commands.command(
        name="move-channel",
        description="Moves a channel into the specific position. Recommend using the get-channel-pos command first.",
    )
    @app_commands.checks.has_any_role(*COMMAND_ROLE_ALLOW_LIST)
    async def move_channel(
        self, interaction: discord.Interaction, channel: discord.TextChannel, pos: int
    ):
        await channel.edit(position=pos)
        await interaction.response.send_message(
            f"{channel.jump_url} moved to position {pos}", ephemeral=True
        )
