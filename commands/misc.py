import asyncio
import os
import random
from typing import Optional

from PIL import Image, ImageSequence
import discord
from discord import app_commands
from discord.ext import commands

from utils import log_utils


@app_commands.guild_only()
class MiscCommandCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.mobile_path = "images/MobileDiscord.png"
        self.embed_path = "images/EmbedDiscord.png"
        self.log_channel = "degen-log"
        self.quote_channel = 472148805127634954
        self.channel_hist = []
        super().__init__()

    @app_commands.command(name="f", description="Pay respects. 'to' is optional.")
    async def pay_respects(
        self, interaction: discord.Interaction, to: Optional[str] = None
    ):
        if to:
            await interaction.response.send_message(
                f"Press 🇫 to pay respects to {to}{'' if to.endswith('.') else '.'}"
            )
        else:
            await interaction.response.send_message("Press 🇫 to pay respects.")
        response = await interaction.original_response()
        await response.add_reaction("🇫")

    @app_commands.command(
        name="quote", description="Quote a previous message through the bot."
    )
    async def quote(self, interaction: discord.Interaction, link: str):
        # https: // discord.com / channels / 119758608765288449 / 428832869398347776 / 1161002383996883058
        # 119758608765288449 / 428832869398347776 / 1161002383996883058
        # GUILD / CHANNEL / MESSAGE
        msg = link.split("/")
        guild = interaction.guild
        channel_id = int(msg[5])
        message_id = int(msg[6])
        channel = guild.get_channel(channel_id)
        message = await channel.fetch_message(message_id)
        tmp_embed = discord.Embed(
            color=message.author.color,
            timestamp=message.created_at,
            description=message.content,
        )
        tmp_embed.add_field(name="", value=message.jump_url)
        tmp_embed.set_author(name=message.author.name, icon_url=message.author.avatar)
        await interaction.response.send_message(embed=tmp_embed)

    @app_commands.command(
        name="quote_submit",
        description="Quote a message into the server's quotes channel (if it exists).",
    )
    async def quote_submit(self, interaction: discord.Interaction, link: str):
        msg = link.split("/")
        guild = interaction.guild
        quotes_channel = discord.utils.find(
            lambda channel: channel.id == self.quote_channel,
            guild.channels,
        )
        if quotes_channel is None:
            raise Exception("Quotes channel not found")
        channel_id = int(msg[5])
        message_id = int(msg[6])
        channel = guild.get_channel(channel_id)
        message = await channel.fetch_message(message_id)
        tmp_embed = discord.Embed(
            color=message.author.color,
            timestamp=message.created_at,
            description=message.content,
        )
        tmp_embed.add_field(name="", value=message.jump_url)
        tmp_embed.set_author(name=message.author.name, icon_url=message.author.avatar)
        await quotes_channel.send(embed=tmp_embed)
        await interaction.response.send_message("Quoted the supplied message!")

    @app_commands.command(name="pfp", description="Receive a user's profile picture.")
    @app_commands.describe(
        ephem="Whether the bot should send the message only to you (True) or post it publicly (False)."
    )
    async def pfp(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        ephem: Optional[bool] = False,
    ):
        avatar = user.display_avatar
        if avatar.is_animated():
            fn = str(user.id) + ".gif"
        else:
            fn = str(user.id) + ".png"
        await avatar.save(fn)
        await interaction.response.send_message(file=discord.File(fn), ephemeral=ephem)
        if os.path.exists(fn):
            os.remove(fn)
        else:
            print(f"Error occurred when deleting file:\t{fn}")

    @app_commands.command(name="mobile")
    async def mobile_image(self, interaction: discord.Interaction, user: discord.User):
        avatar = user.display_avatar
        fn = str(user.id) + "_temp"
        fn_o = "mobile_output.gif"
        frame_list = []
        await avatar.save(fn)
        with Image.open(fn) as im:
            idx = 1
            duration = 0

            for frame in ImageSequence.Iterator(im):
                frame_list.append(self.build_frame(frame, self.mobile_path))
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

        await interaction.response.send_message(file=discord.File(fp=fn_o))

        if os.path.exists(fn):
            os.remove(fn)
        else:
            print(f"Error occurred when deleting file:\t{fn}")
        if os.path.exists(fn_o):
            os.remove(fn_o)
        else:
            print(f"Error occurred when deleting file:\t{fn_o}")

    @app_commands.command(name="rr")
    async def rachael_response(self, interaction: discord.Interaction):
        await interaction.response.send_message("Memeing Rachael:", ephemeral=True)
        chan = interaction.channel
        await chan.send("Yes")
        await asyncio.sleep(1)
        await chan.send("Absolutely")
        await asyncio.sleep(1)
        await chan.send("For sure")
        await asyncio.sleep(1)
        await chan.send("You go queen")

    @app_commands.command(name="dnd_voice")
    async def dnd_voice(self, interaction: discord.Interaction):
        dnd_role_id = 96791637031665664
        for mem in interaction.guild.members:
            if mem.id == interaction.user.id:
                if dnd_role_id in [n.id for n in mem.roles]:
                    dnd_channel_id = 218875887519531008
                    for chan in interaction.guild.channels:
                        if isinstance(chan, discord.VoiceChannel):
                            for mem in chan.members:
                                if dnd_role_id in [n.id for n in mem.roles]:
                                    await mem.move_to(
                                        interaction.guild.get_channel(dnd_channel_id)
                                    )
                                    self.channel_hist.append((mem, chan))
                    await interaction.response.send_message(
                        "Moved connected users to D&D Channel!"
                    )
                else:
                    await interaction.response.send_message(
                        "You must have the relevant D&D role to use this command!",
                        ephemeral=True,
                    )
                break

    @app_commands.command(name="book_voice")
    async def book_voice(self, interaction: discord.Interaction):
        book_role_id = 1198432640462766111
        for mem in interaction.guild.members:
            if mem.id == interaction.user.id:
                if book_role_id in [n.id for n in mem.roles]:
                    book_channel_id = 218875887519531008
                    for chan in interaction.guild.channels:
                        if isinstance(chan, discord.VoiceChannel):
                            for mem in chan.members:
                                if book_role_id in [n.id for n in mem.roles]:
                                    await mem.move_to(
                                        interaction.guild.get_channel(book_channel_id)
                                    )
                                    self.channel_hist.append((mem, chan))
                    await interaction.response.send_message(
                        "Moved connected users to Book Club Channel!"
                    )
                else:
                    await interaction.response.send_message(
                        "You must have the relevant Book Club role to use this command!",
                        ephemeral=True,
                    )
                break

    @app_commands.command(name="eject")
    async def eject(self, interaction: discord.Interaction):
        await interaction.response.defer()
        for mem in interaction.guild.members:
            if mem.id == interaction.user.id:
                if mem.voice.channel:
                    syns = [
                        "the hellscape",
                        "shittown fuckville",
                        "pain and suffering",
                        mem.voice.channel.name,
                        "the devilment",
                        "a place of debauchery and sin",
                    ]
                    ch = random.choice(syns)
                    await interaction.followup.send(
                        f"Ejecting {mem.display_name} from {ch} in 3..."
                    )
                    await asyncio.sleep(1)
                    await interaction.followup.send("2...")
                    await asyncio.sleep(1)
                    await interaction.followup.send("1...")
                    await asyncio.sleep(1)
                    await mem.edit(voice_channel=None)
                    await interaction.followup.send(
                        f"Successfully ejected {mem.display_name} from {ch}."
                    )
                    return
        await interaction.followup.send(
            "Could not find you in any voice calls!", ephemeral=True
        )

    @app_commands.command(name="return_voice")
    async def return_voice(self, interaction: discord.Interaction):
        if self.channel_hist:
            for mem, chan in self.channel_hist:
                await mem.move_to(chan)
            self.channel_hist.clear()
            await interaction.response.send_message(
                "Moved connected voice users to their original channels!"
            )
        else:
            await interaction.response.send_message(
                "No channel history stored for connected voice participants."
            )

    @app_commands.command(name="embed")
    async def embed_image(self, interaction: discord.Interaction, user: discord.User):
        avatar = user.display_avatar
        fn = str(user.id) + "_temp"
        fn_o = "embed_output.gif"
        frame_list = []
        await avatar.save(fn)
        with Image.open(fn) as im:
            idx = 1
            duration = 0

            for frame in ImageSequence.Iterator(im):
                frame_list.append(self.build_frame(frame, self.embed_path))
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

        await interaction.response.send_message(file=discord.File(fp=fn_o))

        if os.path.exists(fn):
            os.remove(fn)
        else:
            print(f"Error occurred when deleting file:\t{fn}")
        if os.path.exists(fn_o):
            os.remove(fn_o)
        else:
            print(f"Error occurred when deleting file:\t{fn_o}")

    def build_frame(self, icon, path):
        mobile_discord = Image.open(path)
        iresize = icon.resize((43, 43), Image.LANCZOS)
        x1, y1 = 221, 148
        x2, y2 = 264, 191
        mask = iresize.convert("RGBA")
        mobile_discord.paste(iresize, (x1, y1, x2, y2), mask)
        return mobile_discord
