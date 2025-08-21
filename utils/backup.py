import discord
from discord import app_commands
from discord.ext import commands, tasks

import asyncio
import redis.asyncio as redis
import os
from datetime import datetime, time, timezone

utc = timezone.utc
times = [time(hour=16, tzinfo=utc)]


@app_commands.guild_only()
class BackupCog(commands.Cog, name="Backups"):
    def __init__(self, bot: commands.Bot, redis_client: redis.Redis):
        self.bot = bot
        self.redis_client = redis_client
        super().__init__()
