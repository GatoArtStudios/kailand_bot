from enum import Enum
import discord

class EstadosUsuario(Enum):
    EN_LINEA = 'EN LINEA'
    DESCONECTADO = 'DESCONECTADO'
    AUSENTE = 'AUSENTE'
    NO_MOLESTAR = 'NO MOLESTAR'

class ColorDiscord(Enum):
    DEFAULT = 0
    AQUA = 1752220
    DARKAQUA = 1146986
    GREEN = 5763719
    DARKGREEN = 2067276
    BLUE = 3447003
    DARKBLUE = 2123412
    PURPLE = 10181046
    DARKPURPLE = 7419530
    LUMINOUSVIVIPINK = 15277667
    DARKVIVIPINK = 11342935
    GOLD = 15844367
    DARKGOLD = 12745742
    ORANGE = 15105570
    DARKORANGE = 11027200
    RED = 15548997
    DARKRED = 10038562
    GREY = 9807270
    DARKGREY = 9936031
    DARKERGREY = 8359053
    LIGHTGREY = 12370112
    NAVY = 3426654
    DARKNAVY = 2899536
    YELLOW = 16776960
    BLACK = 2303786
    BLURPLE = 5793266
    FUCHSIA = 15418782

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