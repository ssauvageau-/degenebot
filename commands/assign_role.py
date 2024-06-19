import os

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from typing import Dict, List


@app_commands.guild_only()
class AssignRoleCommandGroup(app_commands.Group, name="assign-role"):
    def __init__(self, bot: commands.Bot):
        load_dotenv()
        self.bot = bot
        self.PingRoles = (
            "Chaos Lads",
            "professional artists",
            "Tiger Woulds",
            "Aquatic Specialist",
            "Movie Enthusiast",
            "Book Worm",
        )
        super().__init__()

    async def news_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> List[app_commands.Choice[str]]:
        choices = self.PingRoles
        return [
            app_commands.Choice(name=choice, value=choice)
            for choice in choices
            if current.lower() in choice.lower()
        ]

    @app_commands.command(
        name="pings",
        description="Choose which news pings you'd like to receive. Choosing the same role again removes the role.",
    )
    @app_commands.describe(choice="The announcement ping role you want")
    @app_commands.autocomplete(choice=news_autocomplete)
    @app_commands.rename(choice="role")
    async def assign_ping_role(self, interaction: discord.Interaction, choice: str):
        user = interaction.user
        role_scuffed = interaction.guild.roles
        roles = {}
        # guild.roles returns a scuffed object class so we convert it to dict for ease of use
        for x in role_scuffed:
            roles[x.name] = x.id
        if choice in roles:
            ping_role = choice
            ping_role_id = roles[choice]
        else:
            print(
                f"Server {interaction.guild} not configured to accept choice {choice}!"
            )
            return

        # Unassign the role if the user already has it
        user_ping_role = user.get_role(ping_role_id)
        if user_ping_role is not None:
            await user.remove_roles(
                user_ping_role, reason="Unassigning existing ping role"
            )
            await interaction.response.send_message(
                f"Unassigned the {ping_role} role!", ephemeral=True
            )
            return

        # Assign the new ping role to the user
        guild_ping_role = interaction.guild.get_role(ping_role_id)
        await user.add_roles(guild_ping_role, reason="Assigning new ping role")

        await interaction.response.send_message(
            f"Assigned the {ping_role} role!", ephemeral=True
        )
