import os

import discord
import redis.asyncio as redis
from discord.ext import commands
from discord.flags import Intents
from dotenv import load_dotenv

from logging_config import setup_logging
from commands.assign_role import AssignRoleCommandGroup
from commands.tags import TagSystemGroup
from commands.misc import MiscCommandCog
from commands.moderation import ModerationCommandGroup
from commands.rating import RatingCommandGroup
from commands.activity import ActivityCommandGroup
from utils.backup import BackupCog
from events import Events

load_dotenv()
TEST_GUILD_ID = os.getenv("TEST_GUILD")
TEST_GUILD = discord.Object(id=TEST_GUILD_ID)
PRIMARY_GUILD_ID = os.getenv("PRIMARY_GUILD")
PRIMARY_GUILD = discord.Object(id=PRIMARY_GUILD_ID)
TOKEN = os.getenv("DISCORD_TOKEN")
ENV = os.getenv("ENV")


class DegeneBot(commands.Bot):
    def __init__(self, intents: Intents, activity: discord.Activity = None) -> None:
        super().__init__(command_prefix="!", intents=intents, activity=activity)

    async def setup_hook(self):
        redis_client = redis.Redis(host="redis", port=6379, decode_responses=False)
        try:
            await redis_client.ping()
        except Exception as e:
            print("Could not connect to Redis:", e)
            if ENV == "prod":
                exit(1)
        await self.add_cog(Events(self))
        await self.add_cog(MiscCommandCog(self))
        await self.add_cog(BackupCog(self, redis_client))

        self.tree.add_command(AssignRoleCommandGroup(self))
        self.tree.add_command(TagSystemGroup(self))
        self.tree.add_command(ModerationCommandGroup(self))
        self.tree.add_command(RatingCommandGroup(self))
        self.tree.add_command(ActivityCommandGroup(self))

        if ENV == "dev":
            self.tree.copy_global_to(guild=TEST_GUILD)
            await self.tree.sync(guild=TEST_GUILD)
        elif ENV == "prod":
            self.tree.copy_global_to(guild=PRIMARY_GUILD)
            await self.tree.sync(guild=PRIMARY_GUILD)


logging_handler = setup_logging()

bot_activity = discord.Activity(
    type=discord.ActivityType.watching, name="for degen activity."
)
bot = DegeneBot(intents=discord.Intents.all(), activity=bot_activity)

bot.run(TOKEN, log_handler=None)
