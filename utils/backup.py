import io

import discord
from PIL.Image import Image
from discord import app_commands
from discord.ext import commands, tasks

import asyncio
import redis.asyncio as redis
import os
import json
from datetime import datetime, time, timezone
from dotenv import load_dotenv

utc = timezone.utc
times = [time(hour=16, tzinfo=utc)]


async def get_pinned_content(channel: discord.TextChannel):
    res = {}
    pins = await channel.pins()
    for pin in pins:
        if pin.attachments:
            at_list = []
            for atch in pin.attachments:
                at_list.append(await atch.to_file(use_cached=True))
            res.update(
                {
                    pin.id: {
                        "text": pin.clean_content,
                        "attachments": at_list,
                        "created_at": pin.created_at,
                    }
                }
            )
        else:
            res.update(
                {pin.id: {"text": pin.clean_content, "created_at": pin.created_at}}
            )
    return res


@app_commands.guild_only()
class BackupCog(commands.Cog, name="Backups"):
    def __init__(self, bot: commands.Bot, redis_client: redis.Redis):
        load_dotenv()
        self.bot = bot
        self.redis_client = redis_client
        self.backup_files = "backup_files/"
        self.env = os.getenv("ENV")
        if self.env == "prod":
            self.guild = os.getenv("PRIMARY_GUILD")
        else:
            self.guild = os.getenv("TEST_GUILD")
        self.degen_channel = os.getenv("DEGEN_CHANNEL_ID")
        super().__init__()

    @tasks.loop(time=times)
    async def batch_update(self):
        await self.bot.wait_until_ready()
        guild = await self.bot.fetch_guild(self.guild)
        for chan in guild.text_channels:
            if chan.pins():
                content = await get_pinned_content(chan)
                for pin in content:
                    jc = json.dumps(content[pin])
                    await self.redis_client.hset(str(pin), jc)
