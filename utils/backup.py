import io

import discord
from PIL.Image import Image
from discord import app_commands
from discord.ext import commands, tasks

import asyncio
import redis.asyncio as redis
import os
import json
from datetime import datetime, time, timezone, date, timedelta
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
                        "author": pin.author.name,
                    }
                }
            )
        else:
            res.update(
                {
                    pin.id: {
                        "text": pin.clean_content,
                        "created_at": pin.created_at,
                        "author": pin.author.name,
                    }
                }
            )
    return res


@app_commands.guild_only()
class BackupCog(commands.Cog, name="Backups"):
    def __init__(self, bot: commands.Bot, redis_client: redis.Redis):
        load_dotenv()
        self.bot = bot
        self.redis_client = redis_client
        self.env = os.getenv("ENV")
        if self.env == "prod":
            self.guild = os.getenv("PRIMARY_GUILD")
        else:
            self.guild = os.getenv("TEST_GUILD")
        self.degen_channel = os.getenv("DEGEN_CHANNEL_ID")
        self.quotes_channel = 472148805127634954
        super().__init__()

    @tasks.loop(time=times)
    async def batch_update(self):
        if date.today().weekday() != 6:  # Sunday
            return
        await self.bot.wait_until_ready()
        guild = await self.bot.fetch_guild(self.guild)
        await self.bot.get_channel(int(self.degen_channel)).send(
            "# COMMENCING BACK UP PROCESS"
        )
        pdict = await self.redis_client.hgetall("PINS")
        for chan in guild.text_channels:
            if chan.pins():
                content = await get_pinned_content(chan)
                if chan.name in pdict:
                    pdict[chan.name] = pdict[chan.name] | content
                else:
                    pdict[chan.name] = content
        await self.redis_client.hset("PINS", json.dumps(pdict))
        await self.bot.get_channel(int(self.degen_channel)).send("# PINS BACKED UP")
        new_quotes = await self.backup_quotes(guild)
        if new_quotes:
            qdict = await self.redis_client.hgetall("QUOTES")
            await self.redis_client.hset("QUOTES", json.dumps(qdict | new_quotes))
            await self.bot.get_channel(int(self.degen_channel)).send(
                f"# {len(new_quotes)} QUOTES BACKED UP"
            )
        else:
            await self.bot.get_channel(int(self.degen_channel)).send(
                "# NO NEW QUOTES TO BACK UP"
            )
        await self.bot.get_channel(int(self.degen_channel)).send(
            "# BACK UP PROCESS CONCLUDING\n# SEE YOU NEXT WEEK"
        )

    async def backup_quotes(self, guild):
        quotes_channel = discord.utils.find(
            lambda channel: channel.id == self.quotes_channel, guild.channels
        )
        yesterday = date.today() - timedelta(days=1)
        quotes = [
            message
            async for message in quotes_channel.history(limit=1000, before=yesterday)
        ]
        if not quotes:  # no new quotes since yesterday
            return None
        qfx = {}
        for quote in quotes:
            if quote.embeds:
                for embed in quote.embeds:  # should only be one
                    qfx.update(
                        {
                            quote.id: {
                                "text": embed.description,
                                "created_at": quote.created_at,
                                "author": embed.author,
                            }
                        }
                    )
            elif quote.mentions:
                qfx.update(
                    {
                        quote.id: {
                            "text": quote.clean_content,
                            "created_at": quote.created_at,
                            "author": quote.author.name,
                        }
                    }
                )
        return qfx
