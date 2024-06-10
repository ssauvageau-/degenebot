import logging
import random
import re
import os

from PIL import Image, ImageSequence, ImageDraw, ImageFont
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
        self.vel_meme_path = "images/VelMeme.png"

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
    async def vel_event(self, message: discord.Message):
        vel_id = 234455334033293312
        if message.author.id == vel_id and "gay" in message.content.lower():
            msg = message.content

            idx = msg.lower().find("gay")
            ln = 28
            text = msg[: idx + 3] if idx < ln - 3 else msg[idx - (ln - 3) : idx + 3]
            text = text.strip()
            text = "-" + text + "-"
            font = ImageFont.truetype("calibrib.ttf", 16)
            text = self.get_wrapped_text(text, font, 54)

            avatar = message.author.display_avatar
            fn = str(vel_id) + "_temp"
            fn_o = "vel_output.gif"
            frame_list = []
            await avatar.save(fn)
            with Image.open(fn) as im:
                idx = 1
                duration = 0
                for frame in ImageSequence.Iterator(im):
                    frame_list.append(
                        self.build_vel_meme(frame, self.vel_meme_path, text, font)
                    )
                    idx += 1
                    try:
                        duration += im.info["duration"]
                    except KeyError:
                        continue
                frame_duration = int(idx / duration) if duration > 0 else 1000
            frame_list[0].save(
                fn_o,
                save_all=True,
                append_images=frame_list[1:],
                optimize=False,
                duration=frame_duration,
                loop=0,
            )
            await message.reply(file=discord.File(fp=fn_o))
            if os.path.exists(fn):
                os.remove(fn)
            else:
                print(f"Error occurred when deleting file:\t{fn}")
            if os.path.exists(fn_o):
                os.remove(fn_o)
            else:
                print(f"Error occurred when deleting file:\t{fn_o}")

    def build_vel_meme(
        self, icon: Image, path: str, msg: str, font: ImageFont.ImageFont
    ):
        meme = Image.open(path)
        iresize = icon.resize((88, 88), Image.LANCZOS)
        x1, y1 = 29, 112
        x2, y2 = 117, 200
        mask = iresize.convert("RGBA")
        meme.paste(iresize, (x1, y1, x2, y2), mask)
        x1, y1 = 429, 113
        x2, y2 = 517, 201
        mask = iresize.convert("RGBA")
        meme.paste(iresize, (x1, y1, x2, y2), mask)

        draw = ImageDraw.Draw(meme)
        draw.text((30, 40), msg, font=font, fill="#000000")
        return meme

    def get_wrapped_text(self, text: str, font: ImageFont.ImageFont, line_length: int):
        # from https://stackoverflow.com/a/67203353
        lines = [""]
        for word in text.split():
            line = f"{lines[-1]} {word}".strip()
            if font.getlength(line) <= line_length:
                lines[-1] = line
            else:
                lines.append(word)
        return "\n".join(lines)

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
