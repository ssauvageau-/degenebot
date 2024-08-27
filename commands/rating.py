import ast
import base64
import sys
from decimal import Decimal
import os
import json
from typing import Dict, List, Optional

import discord
from discord import ui
from discord import app_commands
from discord.ext import commands

import matplotlib.pyplot as plt


@app_commands.guild_only()
class RatingCommandGroup(app_commands.Group, name="rating"):
    def __init__(self, bot: commands.Bot):
        self.rating_json_path = "json/ratings.json"
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
        self.rating_channel_name = "music-rating-submissions"
        self.fconv = {
            "Instrumentals": "avg_ins",
            "Vocals": "avg_voc",
            "Lyrics": "avg_lyr",
            "Emotion/Feeling": "avg_emo",
            "Overall": "avg_ovr",
        }
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
                else voc / num
                if num > 0
                else 0
            )
            lyr += (
                int(values["Lyrics"])
                if values["Lyrics"] != "N/A"
                else lyr / num
                if num > 0
                else 0
            )
            emo += (
                int(values["Emotion/Feeling"])
                if values["Emotion/Feeling"] != "N/A"
                else emo / num
                if num > 0
                else 0
            )
            ovr += int(values["Overall"])
            num += 1
        self.rating_dict[content]["avg_ins"] = str(
            min(Decimal(ins) / Decimal(num), Decimal(5))
        )
        self.rating_dict[content]["avg_voc"] = str(
            min(Decimal(voc) / Decimal(num), Decimal(5))
        )
        self.rating_dict[content]["avg_lyr"] = str(
            min(Decimal(lyr) / Decimal(num), Decimal(5))
        )
        self.rating_dict[content]["avg_emo"] = str(
            min(Decimal(emo) / Decimal(num), Decimal(5))
        )
        self.rating_dict[content]["avg_ovr"] = str(
            min(Decimal(ovr) / Decimal(num), Decimal(5))
        )

    def get_comments(self, content):
        com = []
        for keys, values in self.rating_dict.get(content).get("ratings").items():
            if values["Comments"]:
                com.append(values["Comments"])
        return com

    def get_highest_field(self, field: str) -> (str, Decimal):
        hk = ""
        hv = 0
        for key, values in self.rating_dict.items():
            if Decimal(values[field]) > Decimal(hv):
                hk = key
                hv = values[field]
        return hk, hv

    def get_lowest_field(self, field: str) -> (str, Decimal):
        hk = ""
        hv = sys.maxsize
        for key, values in self.rating_dict.items():
            if Decimal(values[field]) < Decimal(hv):
                hk = key
                hv = values[field]
        return hk, hv

    def load_ratings(self) -> Dict[str, Dict]:
        with open(self.rating_json_path, "r", encoding="utf-8") as disk_lib:
            return json.loads(disk_lib.read())

    def dump_ratings(self) -> None:
        with open(self.rating_json_path, "w", encoding="utf-8") as disk_lib:
            disk_lib.write(json.dumps(self.rating_dict, sort_keys=True, indent=4))

    def wrap_words(self, text: str, k: int = 3, *, sep: str = None) -> str:
        text = text.strip().split(sep)
        res = ""
        for index, item in enumerate(text):
            # add \n for every k items (it runs at first iteration too because 0%num is equal to 0 ever)
            if index % k == 0:
                res += "\n"
            # add every item to result
            res += item + " "
        # remove first \n and return
        return res[1:].strip()

    async def field_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> List[app_commands.Choice[str]]:
        choices = ["Instrumentals", "Vocals", "Lyrics", "Emotion/Feeling", "Overall"]
        return [
            app_commands.Choice(name=choice, value=choice)
            for choice in choices
            if current.lower() in choice.lower()
        ]

    async def type_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> List[app_commands.Choice[str]]:
        choices = ["Highest", "Lowest"]
        return [
            app_commands.Choice(name=choice, value=choice)
            for choice in choices
            if current.lower() in choice.lower()
        ]

    @app_commands.command(name="stats")
    @app_commands.autocomplete(field=field_autocomplete, extreme=type_autocomplete)
    async def stats(self, interaction: discord.Interaction, extreme: str, field: str):
        if extreme == "Highest":
            ret = self.get_highest_field(self.fconv[field])
        else:
            ret = self.get_lowest_field(self.fconv[field])
        await interaction.response.send_message(
            f"The submission with the {extreme.lower()} `{field}` score is `{ret[0]}` at `{ret[1]}`!"
        )

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
            f"\nTo rate this content, please use the `/rating submit {name_clean}` command."
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

    async def ephem_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> List[app_commands.Choice[str]]:
        choices = ["True", "False"]
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

    @app_commands.command(name="comments")
    @app_commands.autocomplete(content=rating_autocomplete, hidden=ephem_autocomplete)
    async def comments(
        self, interaction: discord.Interaction, content: str, hidden: Optional[str]
    ):
        newline = "\n\t"
        if hidden:
            await interaction.response.send_message(
                f"Here is what people are saying about {content}:"
                f"\n\n\t"
                f"{newline.join(self.get_comments(content))}",
                ephemeral=ast.literal_eval(hidden),
            )
        else:
            await interaction.response.send_message(
                f"Here is what people are saying about {content}:"
                f"\n\n\t"
                f"{newline.join(self.get_comments(content))}"
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
                placeholder="(1->5 or N/A) Rate the instrumental components of the content.",
                required=True,
            )
            voc = ui.TextInput(
                label="Vocals",
                custom_id="voc",
                style=discord.TextStyle.short,
                min_length=0,
                max_length=3,
                placeholder="(1->5 or N/A) Rate the vocal performance of the content.",
                required=True,
            )
            lyr = ui.TextInput(
                label="Lyrics",
                custom_id="lyr",
                style=discord.TextStyle.short,
                min_length=0,
                max_length=3,
                placeholder="(1->5 or N/A) Rate the lyrical quality of the content.",
                required=True,
            )
            emo = ui.TextInput(
                label="Emotion/Feeling",
                custom_id="emo",
                style=discord.TextStyle.short,
                min_length=0,
                max_length=3,
                placeholder="(1->5 or N/A) Rate the emotional impact of the content.",
                required=True,
            )
            com = ui.TextInput(
                label="Comments",
                style=discord.TextStyle.short,
                max_length=300,
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
                vals[i] = int(vals[i])  # if not int-decipherable, goes to except
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

    @app_commands.command(name="download")
    async def download(self, interaction: discord.Interaction):
        self.dump_ratings()
        await interaction.response.send_message(
            file=discord.File("json/ratings.json"), ephemeral=True
        )

    @app_commands.command(name="averages")
    @app_commands.autocomplete(content=rating_autocomplete)
    async def averages(self, interaction: discord.Interaction, content: str):
        k = self.rating_dict.get(content)
        ins = k["avg_ins"]
        voc = k["avg_voc"]
        lyr = k["avg_lyr"]
        emo = k["avg_emo"]
        await interaction.response.send_message(
            f"{content} has average ratings as follows:\n"
            f"\t**Instrumentals**:\t{ins}\n"
            f"\t**Vocals**:\t{voc}\n"
            f"\t**Lyrics**:\t{lyr}\n"
            f"\t**Emotions/Feeling**:\t{emo}\n"
        )

    @app_commands.command(name="drop")
    @app_commands.autocomplete(content=rating_autocomplete)
    @app_commands.checks.has_any_role("Actual Admin")
    async def del_key(self, interaction: discord.Interaction, content: str):
        if interaction.user.id == 95664950743142400:
            await interaction.response.send_message(
                "Sorry, Jared, I do not trust you to not delete TSwift submissions as they appear."
            )
            return
        self.rating_dict.pop(content, None)
        self.dump_ratings()
        await interaction.response.send_message(
            f"{content} has been dropped from the rating JSON successfully.",
            ephemeral=True,
        )

    @app_commands.command(name="graph")
    @app_commands.autocomplete(field=field_autocomplete)
    async def graph(self, interaction: discord.Interaction, field: str):
        keys = []
        vals = []
        for k, v in self.rating_dict.items():
            keys.append(self.wrap_words(k))
            vals.append(float(v[self.fconv[field]]))
        plt.bar(keys, vals)
        plt.suptitle(f"{field} Ratings")
        if field == "Overall":
            plt.ylim(0, 20)
        else:
            plt.ylim(0, 5)
        plt.xticks(list(range(0, len(keys), 1)), keys, rotation=45)
        plt.tight_layout()
        fn = "graph_output.png"
        plt.savefig(fname=fn)
        await interaction.response.send_message(file=discord.File(fn))
        os.unlink(fn)

    @app_commands.command(name="list")
    async def content_list(self, interaction: discord.Interaction):
        merge = []
        nl = "\n"
        for k, v in self.rating_dict.items():
            l = v["content"]
            merge.append(f"[{k}](<{l}>)")
        await interaction.response.send_message(f"{nl.join(merge)}")

    @app_commands.command(name="todo")
    async def todo(self, interaction: discord.Interaction):
        merge = []
        nl = "\n"
        for k, v in self.rating_dict.items():
            if interaction.user.name not in v:
                l = v["content"]
                merge.append(f"[{k}](<{l}>)")
        if len(merge) == 0:
            await interaction.response.send_message(
                f"{interaction.user.mention}, you have rated all submitted content. Nicely done!",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"{interaction.user.mention}, you still have the following pieces of content to rate:\n{nl.join(merge)}",
                ephemeral=True,
            )

    @app_commands.command(name="recompute")
    @app_commands.checks.has_any_role("Actual Admin")
    async def force_recompute(self, interaction: discord.Interaction):
        for k, v in self.rating_dict.items():
            self.recompute_averages(k)
        await interaction.response.send_message(
            "Averages have been recalculated.", ephemeral=True
        )
