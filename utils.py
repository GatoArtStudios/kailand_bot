import discord
from discord.ext import commands
from discord import app_commands
from types_utils import ColorDiscord
from datetime import datetime
from config import API_KEY, END_POINT_API, END_POINT_API_PLAYERS
import requests

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

def datetime_now():
    '''
    Retornara la fecha actual en el formato YYYY-MM-DD
    '''
    # Obtener la fecha actual
    fecha_actual = datetime.now()

    # Formatear la fecha en el formato deseado
    fecha_formateada = fecha_actual.strftime('%Y-%m-%d')

    return fecha_formateada

async def PowerServer(signal: str = 'start'):
    url = f'{END_POINT_API}power'
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    data = {
        "signal": signal
    }
    try:
        respense = requests.post(url, headers=headers, json=data)
        respense.raise_for_status()
        return respense.json()
    except requests.exceptions.HTTPError as err:
        print(err)
        return False
    except Exception as e:
        print(e)
        return False

async def StatusServer():
    '''
    Estados:
    offline,
    starting,
    running,
    stopping
    '''
    url = f'{END_POINT_API}resources'
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    try:
        p = requests.get(url, headers=headers)
        p.raise_for_status()
        r = p.json()
        c = r['attributes']['current_state']

        pl = requests.get(END_POINT_API_PLAYERS)
        pl.raise_for_status()
        rl = pl.json()
        player = rl['players']['online']

        return c, player
    except requests.exceptions.HTTPError as err:
        print(err)
        return False
    except Exception as e:
        print(e)
        return False

async def getUserTicket(interaction: discord.Interaction):
    guild = interaction.guild
    user_name = interaction.channel.name.replace('evento-', '').replace('discord-', ' ').replace('minecraft-', '').replace('launcher-', '').replace('bugs-', '')
    user = discord.utils.get(guild.members, name=user_name)
    return user