import discord
from discord.ext import commands
from discord import app_commands
from types_utils import ColorDiscord

async def color_autocomplete(interaction: discord.Interaction, current: str):
    color_names = [color.name.lower() for color in ColorDiscord]
    return [
        discord.app_commands.Choice(name=color_name, value=color_name)
        for color_name in color_names if current.lower() in color_name
    ][:25]

async def autocomplete_roles(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    roles = interaction.guild.roles
    choices = [app_commands.Choice(name=role.name, value=role.name) for role in roles if current.lower() in role.name.lower()]
    return choices[:25]

async def transform(interaction: discord.Interaction, role: str) -> discord.Role:
    role = discord.utils.get(interaction.guild.roles, name=role)
    if role is None:
        raise app_commands.AppCommandError(f'No se encontró el rol con el nombre: {role}')
    return role
