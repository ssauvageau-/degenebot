import logging
import random
import re

import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone

from utils import log_utils

utc = timezone.utc


class Events(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.logger = logging.getLogger("bot")
        self.log_channel_name = "degen-log"
        self.bot = bot
        self.timeline = {}

    @commands.Cog.listener(name="on_error")
    async def log_error(self, event: str, *args, **kwargs):
        self.logger.error(event)

    @commands.Cog.listener(name="on_app_command_completion")
    async def log_app_command_completion(
        self, interaction: discord.Interaction, command: app_commands.Command
    ):
        self.logger.info(
            f"User {log_utils.format_user(interaction.user)} used command {log_utils.format_app_command_name(command)} in {log_utils.format_channel_name(interaction.channel)}"
        )

    @commands.Cog.listener(name="on_message")
    async def nerd_event(self, message: discord.Message):
        if message.author == self.bot.user:
            return

        if message.content.lower() == "nerd":
            await message.channel.send(message.content)
            await message.delete()
            self.logger.info(f"nerd event triggered on message {message.jump_url}")

    @commands.Cog.listener(name="on_message")
    async def based_event(self, message: discord.Message):
        if message.author == self.bot.user:
            return

        if message.content.lower() == "based":
            if random.randint(1, 10) == 2:
                await message.reply(content="Based? Based on what?")

    @commands.Cog.listener(name="on_message")
    async def thinkematic_event(self, message: discord.Message):
        if message.author == self.bot.user:
            return

        thinkematics_tm = {
            "🤔😉": "<:winking:359819933711859713>",
            "🤔🇯🇵": "<:weebthink:359798823725432842>",
            "🤔🖕": "<:upthink:359820561305829386>",
            "🤔☯": "<:thinkyang:359822049650147339>",
            "🤔🌊": "<:thinkwave:359800247876059139>",
            "🤔✝️": "<:thinkusVult:537783872595689487>",
            "🤔👍": "<:thinkup:359823000159387649>",
            "🤔😐": "<:thinkstare:359820274532614144>",
            "🤔🔄": "<a:fidgetthink:1153410621057011762>",
            "🤔🔃": "<a:fidgetthink_alt:1153411438271013065>",
            "🤔😡": "<:thinkrage:359798824404910080>",
            "🤔🍆": "<:thinkplant:359822667655938048>",
            "🤔💻": "<:thinkpad:359821250484502540>",
            "🤔😕": "<:thinkfusing:359822865584881690>",
            "🤔🐟": "<:thinkfish:359822611191955466>",
            "🤔💦": "<:thinkdrops:359821539392225291>",
            "🤔🤔": "<:thinkception:359822479147008000>",
            "🤔⬜": "<:squarethink:359821163817467904>",
            "🤔🥔": "<:spudthink:1160997520474902569>",
            "🤔🦀": "<:crabthink:1175152963199701062>",
            "🤔🎩": "<:mthinking:359821640340733952>",
            "🤔👈": "<:leftythink:359821079264624640>",
            "🤔👏": "<:clapking:359798826388815889>",
            "🤔🍞": "<:breading:359821383401865228>",
            "🤔🍺": "<:beerthink:359821722439909376>",
            "🤔😫": "<:thinkyawn:359821867634393089>",
            "🤔🍿": "<:thinkcorn:376774691144204288>",
            "🤔🅱️": "<:bhinking:537783061656371220>",
            "🤔💩": "<:poopthink:538566107687288862>",
            "🤔👀": "<:thinkeyes:359798823486226443>",
            "🤔👌": "<:ok_thinking:359798825763995648>",
            "🤔⬆️⬆️⬇️⬇️⬅️➡️⬅️➡️🇧🇦": f"{message.author.mention} is a nerd! 🤓",
            "<:thonking:327364004211064832><:thonking:327364004211064832>": "<a:thonkered:540696116069400607>",
            "🤔🐦": "<:mayayy:1153451055657517077>",
            "🤔🔥": "<:finethink:1153504940178817034>",
            "<:kappaScorv:562136888731762688><:kappaScorv:562136888731762688>": "<:scorvChaos:655350057205235712>",
            "<:kappaScorv:562136888731762688>🔫": "<:scorvgun:792202763379015681>",
        }

        pruned = message.content.replace(" ", "")
        think = thinkematics_tm.get(pruned)
        if think is not None:
            think_message = await message.channel.send(think)
            await message.delete()
            self.logger.info(
                f"Thinkematics {think} triggered by {message.author.display_name} {think_message.jump_url}"
            )

    @commands.Cog.listener(name="on_message")
    async def masked_url_event(self, message: discord.Message):
        if message.author.bot:
            return

        log_channel = discord.utils.find(
            lambda channel: channel.name == self.log_channel_name,
            message.guild.channels,
        )
        if log_channel is None:
            raise Exception("Log channel not found")

        masked_url_pattern = r"\[(?P<mask>.+)\]\((?P<url>.*)\)"
        for masked_url in re.finditer(masked_url_pattern, message.content):
            mask = masked_url.group("mask")
            url = masked_url.group("url")

            log_embed = discord.Embed(
                color=discord.Color.yellow(),
                title="Masked URL in message",
                timestamp=message.created_at,
            )
            log_embed.set_author(
                name=message.author.display_name,
                icon_url=message.author.display_avatar.url,
            )
            log_embed.add_field(name="Message", value=message.jump_url, inline=True)
            log_embed.add_field(name="Mask", value=f"`{mask}`", inline=True)
            log_embed.add_field(name="URL", value=f"`{url}`", inline=True)

            await log_channel.send(embed=log_embed)
            self.logger.info(
                f"Masked URL [{mask}]({url}) posted in {log_utils.format_channel_name(message.channel)} {message.jump_url}"
            )
