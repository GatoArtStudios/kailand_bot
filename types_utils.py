from enum import Enum
import discord

class EstadosUsuario(Enum):
    EN_LINEA = 'EN LINEA'
    DESCONECTADO = 'DESCONECTADO'
    AUSENTE = 'AUSENTE'
    NO_MOLESTAR = 'NO MOLESTAR'

def ConverStatus(status: discord.Status):
    '''
    Retorna el estado en el que se encuentra el usuario.
    ```
        if status == discord.Status.online:
            return EstadosUsuario.EN_LINEA
        elif status == discord.Status.offline:
            return EstadosUsuario.DESCONECTADO
        elif status == discord.Status.idle:
            return EstadosUsuario.AUSENTE
        elif status == discord.Status.dnd:
            return EstadosUsuario.NO_MOLESTAR
        else:
            return EstadosUsuario.DESCONECTADO
    ```
    '''
    if status == discord.Status.online:
        return EstadosUsuario.EN_LINEA
    elif status == discord.Status.offline:
        return EstadosUsuario.DESCONECTADO
    elif status == discord.Status.idle:
        return EstadosUsuario.AUSENTE
    elif status == discord.Status.dnd:
        return EstadosUsuario.NO_MOLESTAR
    else:
        return EstadosUsuario.DESCONECTADO