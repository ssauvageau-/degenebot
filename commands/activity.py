import json
import os

from typing import Dict, List

import discord
from discord import ui
from discord.ui import View
from discord import app_commands
from discord.ext import commands


@app_commands.guild_only()
class ActivityCommandGroup(app_commands.Group, name="activity"):
    def __init__(self, bot: commands.Bot):
        self.act_json_path = "json/activity.json"
        try:
            self.act_dict = self.load_acts()
        except json.decoder.JSONDecodeError:
            self.act_dict = {}
        except FileNotFoundError:
            self.act_dict = {}
            if not os.path.exists("json"):
                os.makedirs("json")
            os.close(os.open(self.act_json_path, os.O_CREAT))
        self.bot = bot
        super().__init__()

    def load_acts(self) -> Dict[str, Dict]:
        with open(self.act_json_path, "r", encoding="utf-8") as disk_lib:
            return json.loads(disk_lib.read())

    def dump_acts(self) -> None:
        with open(self.act_json_path, "w", encoding="utf-8") as disk_lib:
            disk_lib.write(json.dumps(self.act_dict, sort_keys=True, indent=4))

    @app_commands.command(
        name="enumerate",
        description="Lists all activities you are a part of, and with whom.",
    )
    async def enumerate(self, interaction: discord.Interaction):
        user = interaction.user.global_name
        if not self.act_dict[user]:
            await interaction.response.send_message(
                "You do not partake in any activities with others at this time.",
                ephemeral=True,
            )
            return
        a_list = self.act_dict[user]
        users = list(self.act_dict.keys())
        users.remove(user)
        res = ["You partake in the following activities with the following users:\n```"]
        for u in users:
            tmp = []
            for act in a_list:
                if act in self.act_dict[u]:
                    tmp.append(act)
            if tmp:
                res.append(f"\t{u}:\n")
                for act in tmp:
                    res.append(f"\t\t{act}\n")
        res.append("```")
        await interaction.response.send_message("".join(res), ephemeral=True)

    @app_commands.command(
        name="new", description="Submit a new joint activity for two or more users."
    )
    async def new_activity(self, interaction: discord.Interaction, activity_name: str):
        min_u = 2
        max_u = 25

        oself = self

        class MemberSelect(View):
            def add_activity(self, users, tname):
                for user in users:
                    if user not in oself.act_dict:
                        oself.act_dict[user] = [tname]
                    else:
                        oself.act_dict[user].append(tname)

                oself.dump_acts()

            @ui.select(
                cls=ui.UserSelect,
                placeholder=f"Select users...",
                min_values=2,
                max_values=25,
            )
            async def user_select(
                self, inter: discord.Interaction, select: ui.UserSelect
            ):
                self.add_activity([u.global_name for u in select.values], activity_name)
                await inter.response.send_message(
                    f"Added {len(select.values)} users to the {activity_name} activity.",
                    ephemeral=True,
                )

        members = MemberSelect()

        await interaction.response.send_message(
            f"{interaction.user.mention}, choose {min_u} to {max_u} users to partake in this activity!",
            view=members,
            ephemeral=True,
        )

    @app_commands.command(
        name="mutual", description="Lists activities shared by selected users."
    )
    async def find_mutual(self, interaction: discord.Interaction):
        min_u = 2
        max_u = 25

        oself = self

        class MemberSelect(View):
            def find_mut(self, users) -> str:
                buckets = {}
                res = ["The given users share the following activities:\n```"]
                for user in users:
                    if user not in oself.act_dict:
                        return f"{user} does not partake in any current activities! Add one with `/activity new`"
                    for act in oself.act_dict[user]:
                        if act in buckets:
                            buckets[act] += 1
                        else:
                            buckets[act] = 1
                for act in buckets:
                    if buckets[act] == len(users):
                        res.append(f"\t{act}\n")
                if len(res) == 1:
                    return "The given users do not share an activity between them. :("
                res.append("```")
                return "".join(res)

            @ui.select(
                cls=ui.UserSelect,
                placeholder=f"Select users...",
                min_values=2,
                max_values=25,
            )
            async def user_select(
                self, inter: discord.Interaction, select: ui.UserSelect
            ):
                res = self.find_mut([u.global_name for u in select.values])
                await inter.response.send_message(res, ephemeral=True)

        members = MemberSelect()

        await interaction.response.send_message(
            f"{interaction.user.mention}, choose {min_u} to {max_u} users to find an activity between.",
            view=members,
            ephemeral=True,
        )

    async def activity_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> List[app_commands.Choice[str]]:
        choices = set()
        user = interaction.user.global_name
        if user not in self.act_dict:
            return []
        for act in self.act_dict[interaction.user.global_name]:
            choices.add(act)
        return [
            app_commands.Choice(name=choice, value=choice)
            for choice in choices
            if current.lower() in choice.lower()
        ]

    @app_commands.command(
        name="remove-self",
        description="Removes the given activity from your roster of activities. Only affects you.",
    )
    @app_commands.autocomplete(activity=activity_autocomplete)
    async def remove_self_from_activity(
        self, interaction: discord.Interaction, activity: str
    ):
        user = interaction.user.global_name
        if user not in self.act_dict:
            await interaction.response.send_message(
                "You do not currently partake in any activities.", ephemeral=True
            )
        elif activity not in self.act_dict[user]:
            await interaction.response.send_message(
                f"You do not currently partake in {activity}.", ephemeral=True
            )
        self.act_dict[user].remove(activity)
        if len(self.act_dict[user]) == 0:
            self.act_dict.pop(user)
        self.dump_acts()
        await interaction.response.send_message(
            f"You no longer partake in {activity}.", ephemeral=True
        )

    @app_commands.command(
        name="rename",
        description="Renames the given activity for all users that partake in it.",
    )
    @app_commands.autocomplete(activity=activity_autocomplete)
    async def rename_activity(
        self, interaction: discord.Interaction, activity: str, new_name: str
    ):
        for user in self.act_dict:
            for i in range(len(self.act_dict[user])):
                if self.act_dict[user][i] == activity:
                    self.act_dict[user][i] = new_name
        await interaction.response.send_message(
            f"Renamed {activity} to {new_name} for all users.", ephemeral=True
        )
        self.dump_acts()
