import discord
from discord.ext import commands
from discord import app_commands


async def autocomplete_roles(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    roles = interaction.guild.roles
    choices = [app_commands.Choice(name=role.name, value=role.name) for role in roles if current.lower() in role.name.lower()]
    return choices[:25]

async def transform(interaction: discord.Interaction, role: str) -> discord.Role:
    role = discord.utils.get(interaction.guild.roles, name=role)
    if role is None:
        raise app_commands.AppCommandError(f'No se encontró el rol con el nombre: {role}')
    return role
