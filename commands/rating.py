import base64
import os
import json
from typing import Dict, List

import discord
from discord import ui
from discord import app_commands
from discord.ext import commands

from dotenv import load_dotenv


@app_commands.guild_only()
class RatingCommandGroup(app_commands.Group, name="rate"):
    def __init__(self, bot: commands.Bot):
        load_dotenv()
        self.rating_json_path = os.getenv("RATINGS_JSON_PATH")
        try:
            self.rating_dict = self.load_ratings()
        except json.decoder.JSONDecodeError:
            self.rating_dict = {}
        except FileNotFoundError:
            self.rating_dict = {}
            if not os.path.exists("json"):
                os.makedirs("json")
            os.close(os.open(self.rating_json_path, os.O_CREAT))
        self.bot = bot
        self.rating_channel_name = "music-ratings"
        super().__init__()

    def recompute_averages(self, content):
        num = ins = voc = lyr = emo = ovr = 0
        for keys, values in self.rating_dict.get(content).get("ratings").items():
            ins += (
                int(values["Instrumentals"])
                if values["Instrumentals"] != "N/A"
                else ins / num
                if num > 0
                else 0
            )
            voc += (
                int(values["Vocals"])
                if values["Vocals"] != "N/A"
                else ins / num
                if num > 0
                else 0
            )
            lyr += (
                int(values["Lyrics"])
                if values["Lyrics"] != "N/A"
                else ins / num
                if num > 0
                else 0
            )
            emo += (
                int(values["Emotion/Feeling"])
                if values["Emotion/Feeling"] != "N/A"
                else ins / num
                if num > 0
                else 0
            )
            ovr += int(values["Overall"])
            num += 1
        self.rating_dict[content]["avg_ins"] = ins / num
        self.rating_dict[content]["avg_voc"] = voc / num
        self.rating_dict[content]["avg_lyr"] = lyr / num
        self.rating_dict[content]["avg_emo"] = emo / num
        self.rating_dict[content]["avg_ovr"] = ovr / num

    def get_comments(self, content):
        com = []
        for keys, values in self.rating_dict.get(content).get("ratings").items():
            if values["Comments"]:
                com.append(values["Comments"])
        return com

    def load_ratings(self) -> Dict[str, Dict]:
        with open(self.rating_json_path, "r", encoding="utf-8") as disk_lib:
            return json.loads(disk_lib.read())

    def dump_ratings(self) -> None:
        with open(self.rating_json_path, "w", encoding="utf-8") as disk_lib:
            disk_lib.write(json.dumps(self.rating_dict, sort_keys=True))

    def encode_rating_data(self, data: str) -> str:
        return base64.b64encode(data.encode("utf-8")).decode("utf-8")

    def decode_rating_data(self, data: str) -> str:
        return base64.b64decode(data.encode("utf-8")).decode("utf-8")

    async def rating_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> List[app_commands.Choice[str]]:
        choices = [*self.rating_dict]
        ratings = [
            app_commands.Choice(name=choice, value=choice)
            for choice in choices
            if current.lower() in choice.lower()
        ]
        if len(ratings) > 25:
            return ratings[:25]
            # Discord autocomplete only supports 25 elements
            # Without this, users are not shown any elements of the tag list when total tags > 25
        return ratings

    @app_commands.command(
        name="new",
        description="Submit a new piece of content to be rated by your peers.",
    )
    async def submit_for_ratings(
        self, interaction: discord.Interaction, name: str, content: str
    ):
        name_clean = name.strip()
        content_clean = content.strip()
        if name_clean in self.rating_dict:
            await interaction.response.send_message(
                f"Tag `{name_clean}` already exists!", ephemeral=True
            )
            return
        rating_channel = discord.utils.find(
            lambda channel: channel.name == self.rating_channel_name,
            interaction.guild.channels,
        )
        if rating_channel is None:
            raise Exception("Music Rating channel not found")
        msg = await self.bot.get_channel(int(rating_channel.id)).send(
            f"{interaction.user.mention} has submitted `{name_clean}` for rating by you, their peers!"
            f"\n\t\t{content_clean}"
            f"\nTo rate this content, please use the `/rate submit {name_clean}` command."
        )
        self.rating_dict[name_clean] = {
            "content": content_clean,
            "ratings": {},
            "avg_ins": 0,
            "avg_voc": 0,
            "avg_lyr": 0,
            "avg_emo": 0,
            "avg_ovr": 0,
        }
        self.dump_ratings()
        await interaction.response.send_message(
            f"`{name_clean}` has been submitted for review by your peers. See {msg.jump_url}",
            ephemeral=True,
        )

    @app_commands.command(
        name="submit", description="Rate a piece of content from your peers"
    )
    @app_commands.autocomplete(content=rating_autocomplete)
    async def submit_rating(self, interaction: discord.Interaction, content: str):
        class RatingModal(ui.Modal, title=f"{content} Rating"):
            ins = ui.TextInput(
                label="Instrumentals",
                custom_id="ins",
                style=discord.TextStyle.short,
                min_length=0,
                max_length=3,
                placeholder="Rate the instrumental components of the content.",
                required=True,
            )
            voc = ui.TextInput(
                label="Vocals",
                custom_id="voc",
                style=discord.TextStyle.short,
                min_length=0,
                max_length=3,
                placeholder="Rate the vocal performance of the content.",
                required=True,
            )
            lyr = ui.TextInput(
                label="Lyrics",
                custom_id="lyr",
                style=discord.TextStyle.short,
                min_length=0,
                max_length=3,
                placeholder="Rate the lyrical quality of the content.",
                required=True,
            )
            emo = ui.TextInput(
                label="Emotion/Feeling",
                custom_id="emo",
                style=discord.TextStyle.short,
                min_length=0,
                max_length=3,
                placeholder="Rate the emotional impact of the content.",
                required=True,
            )
            com = ui.TextInput(
                label="Comments",
                style=discord.TextStyle.short,
                row=4,
                placeholder="",
                required=False,
            )

            async def on_submit(self, interaction: discord.Interaction):
                await interaction.response.send_message(
                    f"Thank you for rating `{content}`, {interaction.user.mention}!\nYour response has been recorded.",
                    ephemeral=True,
                )
                self.stop()

        rm = RatingModal()
        await interaction.response.send_modal(rm)
        await rm.wait()
        vals = [rm.ins.value, rm.voc.value, rm.lyr.value, rm.emo.value]
        overall = 0
        for i in range(len(vals)):
            try:
                vals[i] = int(vals[i])  # if not an int, goes to except
                vals[i] = max(
                    min(5, int(vals[i])), 1
                )  # constrict ratings to 1->5 range
                overall += vals[i]
            except ValueError:  # value was a str
                vals[i] = "N/A"
        self.rating_dict[content]["ratings"][str(interaction.user.name)] = {
            "Instrumentals": vals[0],
            "Vocals": vals[1],
            "Lyrics": vals[2],
            "Emotion/Feeling": vals[3],
            "Overall": overall,
            "Comments": rm.com.value,
        }
        self.recompute_averages(content)
        self.dump_ratings()