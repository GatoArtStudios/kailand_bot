import discord
from discord.ext import commands
from discord.ext import tasks
from discord import app_commands
from discord.ui import View, Select, Button
import logging
import ping3
import time
import datetime
import socket
import aiohttp
import json
import asyncio
import ui
from  sql import SQL
import utils
import config
import typing
from config import user_ticket, ID_DEVELOPER, ID_ROLE_HELPER, ID_ROLE_MOD, ID_ROLE_TECN, TICKET_CATEGORY_PRIVATE_ID, TICKET_CATEGORY_MEDIUN_ID, TICKET_CATEGORY_IMPORT_ID
from types_utils import EstadosUsuario, ConverStatus, ColorDiscord
from log import logging
from config import CHANNEL_STATUS_ID as channel_status_id, MESSAGE_STATUS_ID as msg_status_id

# ? ------------------------------------ Configuracion de la base de datos ------------------------------------

db = SQL()

# TODO: Crea tablas en la base de datos
db.run("CREATE TABLE IF NOT EXISTS users (id BIGINT PRIMARY KEY, name VARCHAR(255), time BIGINT)")
db.run("CREATE TABLE IF NOT EXISTS roles (id_rol BIGINT PRIMARY KEY, rol_name VARCHAR(255), id_server BIGINT, server_name VARCHAR(255))")
db.run("CREATE TABLE IF NOT EXISTS datetime (id BIGINT AUTO_INCREMENT PRIMARY KEY, user_id BIGINT, user_name VARCHAR(255), timestamp BIGINT, estado VARCHAR(255))")
db.run("CREATE TABLE IF NOT EXISTS del_message (id BIGINT AUTO_INCREMENT PRIMARY KEY, server VARCHAR(255), channel VARCHAR(255), message VARCHAR(255), message_author VARCHAR(255), message_author_id BIGINT, user_action VARCHAR(255), user_action_id BIGINT, timestamp BIGINT)")
data = db.consulta("SELECT * FROM users").fetchall()


# ? ------------------------------------ Variables ------------------------------------

user_online = {}
user_register = {}
user_spam = {}
datetime_actual = utils.datetime_now()
channel_status: discord.TextChannel = None
message_status_embed: discord.Message = None
embed_status = ui.StatusServerEmbed()
# Servidor de minecraft
estado = ''
timestamp = int(datetime.datetime.now().timestamp())

# ? -------------------------------------- Configuracion de Discord --------------------------------------

# class KailandBot(commands.Bot)

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.presences = True
intents.members = True

bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def setup_hook():
    bot.add_view(ui.TicketSelectView())
    bot.add_view(ui.TicketCloseView())
    bot.add_view(ui.REGISTER(user_online, db))
    bot.add_view(ui.ServerStatusView())
    # bot.add_dynamic_items(DynamicButton) Para botones dinamicos

# ?------------------------------------ Eventos ------------------------------------

@bot.event
async def on_ready():
    global message_status_embed, channel_status
    print('Sincronizando datos del servidor')
    logging.info(f'( {bot.user.name} Se a conectado a Discord!, ID" ({bot.user.id})')
    # Seteamos el estado del bot
    custom_emoji = discord.PartialEmoji(name='😎', animated=False)
    presence = discord.CustomActivity(
            name='🔫 ¡Jugando a Kailand V! 🔫',
        emoji=custom_emoji
    )
    logging.info('Registrando árbol de comandos')
    # ? ------------------------------------ Buscamos y editamos el mensaje que se encarga de registrar el ingreso ------------------------------------
    try:
        # ? ------------------------------------ Buscamos los usuarios a monitoria la actividad ------------------------------------
        # TODO: Consultamos todos los roles de la base de datos
        server = db.consulta("SELECT * FROM roles").fetchall()
        if len(server) > 0: # Verificamos si hay roles guardados
            for i in server: # Iteramos los roles
                # print(i)
                server = bot.get_guild(i[2]) # Obtenemos el servidor con el id
                if server: # Verificamos si el servidor existe
                    role = discord.utils.get(server.roles, id=i[0]) # Obtenemos el rol con el id
                    if role: # Verificamos si el rol existe
                        for menber in role.members: # Iteramos los miembros del rol
                            user_id, user_name, status = menber.id, menber.name, menber.status
                            logging.info(f'Usuario registrado: {user_id}, {user_name}')
                            # continue
                            if user_id and user_name:
                                if user_id not in user_register:
                                    user_register[user_id] = {'estado': ConverStatus(status), 'name': user_name}
                                else:
                                    user_register[user_id].update({'estado': ConverStatus(status), 'name': user_name})
                                # TODO: Guardamos el usuario en la base de datos
                                db.insertar("INSERT INTO users (id, name, time) VALUES (%s, %s, %s)", (user_id, user_name, 0))
                            else:
                                continue
        users_valided_online = db.consulta("SELECT * FROM datetime").fetchall()
        if len(users_valided_online) > 0:
            for user in users_valided_online:
                # print(f'Id: {user[1]}, Estado: {user[4]}, Nombre: {user[2]}')
                if user[4] == 'EN LINEA':
                    user_online[user[1]] = {'estado': EstadosUsuario.EN_LINEA, 'name': user[2]}
                else:
                    if user[1] in user_online:
                        del user_online[user[1]]

        # Obtenemos el mensaje y lo almacenamos en una variable
        channel_status = bot.get_channel(channel_status_id)
        if channel_status is not None:
            try:
                message_status_embed = await channel_status.fetch_message(msg_status_id)

                if message_status_embed is None:
                    print('Error al obtener el mensaje del estado del servidor')
                else:
                    print(f'Obteniendo el mensaje de estado del servidor: {message_status_embed.embeds}' )
            except Exception as e:
                logging.error(f'Error al obtener el mensaje de estado del servidor: {e}')
                print(f'Error al obtener el mensaje de estado del servidor: {e}')
    # ? ------------------------------------ Sincronizamos comandos y actualizamos el estado del bot ------------------------------------
        synced = await bot.tree.sync()
        logging.info(f'Sincronizando {len(synced)} commando (s)')
        print(f'Sincronizando {len(synced)} commando (s)')
    except Exception as e:
        logging.error(f'Tipo de error {e}')
    # Responde al evento colocando el estado de la actividad personalizada
    await bot.change_presence(activity=presence)
    print('Bot iniciado correctamente.')

# ? ------------------------------------ Evento de presencia ------------------------------------
@bot.event
async def on_presence_update(before: discord.Member, after: discord.Member):
    if after.id in user_register and after.id in user_online and after.status != before.status:

        if after.status == discord.Status.online and before.status != discord.Status.online and after.status != before.status:
            if user_online[after.id]['estado'] != EstadosUsuario.EN_LINEA:
                user_online[after.id] = {'estado': EstadosUsuario.EN_LINEA, 'name': after.display_name}
                # TODO: Guardamos el usuario en la base de datos
                db.datetime(after.id, after.display_name, EstadosUsuario.EN_LINEA)
                logging.info(f'Estado: {EstadosUsuario.EN_LINEA}, {after.display_name}, ({after.id})')

        elif after.status == discord.Status.dnd and before.status != discord.Status.dnd  and after.status != before.status:
            if user_online[after.id]['estado'] != EstadosUsuario.NO_MOLESTAR:
                user_online[after.id] = {'estado': EstadosUsuario.NO_MOLESTAR, 'name': after.display_name}
                # TODO: Guardamos el usuario en la base de datos
                db.datetime(after.id, after.display_name, EstadosUsuario.NO_MOLESTAR)
                logging.info(f'Estado: {EstadosUsuario.NO_MOLESTAR}, {after.display_name}, ({after.id})')

        elif after.status == discord.Status.idle and before.status != discord.Status.idle  and after.status != before.status:
            if user_online[after.id]['estado'] != EstadosUsuario.AUSENTE:
                user_online[after.id] = {'estado': EstadosUsuario.AUSENTE, 'name': after.display_name}
                # TODO: Guardamos el usuario en la base de datos
                db.datetime(after.id, after.display_name, EstadosUsuario.AUSENTE)
                logging.info(f'Estado: {EstadosUsuario.AUSENTE}, {after.display_name}, ({after.id})')

        elif after.status == discord.Status.invisible and before.status != discord.Status.invisible  and after.status != before.status:
            if user_online[after.id]['estado'] != EstadosUsuario.DESCONECTADO:
                user_online[after.id] = {'estado': EstadosUsuario.DESCONECTADO, 'name': after.display_name}
                # TODO: Guardamos el usuario en la base de datos
                db.datetime(after.id, after.display_name, EstadosUsuario.DESCONECTADO)
                logging.info(f'Estado: {EstadosUsuario.DESCONECTADO}, {after.display_name}, ({after.id})')

        elif after.status == discord.Status.offline and before.status != discord.Status.offline  and after.status != before.status:
            if user_online[after.id]['estado'] != EstadosUsuario.DESCONECTADO:
                user_online[after.id] = {'estado': EstadosUsuario.DESCONECTADO, 'name': after.display_name}
                # TODO: Guardamos el usuario en la base de datos
                db.datetime(after.id, after.display_name, EstadosUsuario.DESCONECTADO)
                logging.info(f'Estado: {EstadosUsuario.DESCONECTADO}, {after.display_name}, ({after.id})')

# ? ------------------------------------ Eventos de mensajes ------------------------------------

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    # Verificacion si el usuario no tiene autorizacion para mencionar a todos los usuarios
    if not message.author.guild_permissions.mention_everyone and '@everyone' in message.content:
        await message.delete()
        if message.author.id in user_spam:
            user_spam[message.author.id] += 1
        else:
            user_spam[message.author.id] = 1
        if user_spam[message.author.id] >= 3:
            try:
                timeout_expired = datetime.timedelta(seconds=60)
                await message.author.timeout(timeout_expired, reason="Esta haciendo spam mencionando a todos los usuarios, posible cuenta comprometida.")
            except Exception as e:
                print("Error al aislar a cuenta comprometida: " + message.author.display_name)
            user_spam[message.author.id] = 0

@bot.event
async def on_message_delete(message: discord.Message):
    if message.author.bot:
        return
    print(f'{message.channel.name}, {message.guild.name}, {message.author.name}, {message.author.id}, {message.content}')

    await asyncio.sleep(1)

    async for entry in message.guild.audit_logs(limit=1, action=discord.AuditLogAction.message_delete):
        if entry.target.id == message.author.id:
            print(f'Mensaje eliminado por: {entry.user.display_name}, ID: {entry.user.id}')
            # TODO: Guardamos el registro del mensaje eliminado en la base de datos
            db.del_message(message, entry.user.display_name, entry.user.id)
            break


# ? -------------------------------------- Definición de comandos --------------------------------------

@bot.tree.command(name='info', description='Ver información del bot')
@commands.has_permissions(administrator=True, manage_guild=True)
async def info(interaction: discord.Interaction):
    # Verificar si el usuario tiene permisos de administrador o gestionar servidor
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("No tienes permisos para usar este comando.", ephemeral=True)
        return
    await interaction.response.send_message(f'El bot se llama {bot.user.name} y su ID es {bot.user.id}', ephemeral=True)

@bot.tree.command(name='estadisticas', description='Muestra las estadísticas del los usuarios registrados')
async def update_state(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("No tienes permisos para usar este comando.", ephemeral=True)
        return
    await interaction.response.send_message(f'recopilando estadisticas, por favor espere', ephemeral=True)
    # TODO: Mostramos las estadísticas de los usuarios registrados
    stats = db.get_user_statistics()
    #     print(stats)
    # response = "# Estadísticas de tiempo en línea por día:\n"
    # for row in stats:
    #     horas = round(row[3])
    #     response += f"- Usuario: {row[1]} ({row[0]}), Día: {row[2]}, Horas en línea: {horas}\n"
    # await interaction.user.send(response)

@bot.tree.command(name='insertar', description='Inserta un nuevo usuario a la base de datos.')
@commands.has_permissions(administrator=True, manage_guild=True)
async def insertar(interaction: discord.Interaction, usuario: discord.Member):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("No tienes permisos para usar este comando.", ephemeral=True)
        return
    # TODO: Guardamos en la base de datos el usuario elegido por el comando
    insert = db.insertar("INSERT INTO users (id, name, time) VALUES (%s, %s, %s)", (usuario.id, usuario.display_name, 0))
    if insert:
        await interaction.response.send_message(f'# Registro exitoso. \nInsertado {usuario.display_name} ({usuario.id})', ephemeral=True)
    else:
        await interaction.response.send_message(f'# Registro fallido. \nNo se inserto {usuario.display_name} ({usuario.id}), el usuario puede estar ya registrado.', ephemeral=True)

@bot.tree.command(name='borrar', description='Borra un usuario de la base de datos')
@commands.has_permissions(administrator=True, manage_guild=True)
async def borrar(interaction: discord.Interaction, usuario: discord.Member):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("No tienes permisos para usar este comando.", ephemeral=True)
        return
    # TODO: Eliminamos un usuario elegido de la base de datos
    del_user = db.insertar("DELETE FROM users WHERE id = %s", (usuario.id,))
    if del_user:
        await interaction.response.send_message(f'# Usuario borrado. \nBorrado {usuario.display_name} ({usuario.id})', ephemeral=True)
    else:
        await interaction.response.send_message(f'# Error al eliminar. \nNo se borro {usuario.display_name} ({usuario.id}), el usuario no existe.', ephemeral=True)

@bot.tree.command(name='get_users', description='Muestra los usuarios de la base de datos.')
@commands.has_permissions(administrator=True, manage_guild=True)
async def consulta(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("No tienes permisos para usar este comando.", ephemeral=True)
        return
    # TODO: Obtenemos todos los usuarios registrados en la base de datos
    data = db.consulta("SELECT * FROM users").fetchall()
    if len(data) == 0:
        await interaction.response.send_message(
            f'# No hay usuarios registrados.\n- Por favor inserte un usuario.\n**Nota:** Puedes usar el comando `/insertar` + Nombre de usuario, para agregar nuevos usuarios',
            ephemeral=True
        )
    else:
        respon = ''
        for i in data:
            respon += f'- Usuario: {i[1]}, ID: {i[0]}, Tiempo: {i[2]}\n'
        if len(json.dumps(respon, ensure_ascii=False, indent=2)) <= 1900:
            await interaction.response.send_message(f'# consulta exitosa de usuarios. \n {respon}', ephemeral=True)
        else:
            await interaction.response.send_message(f'# consulta exitosa de usuarios. \n- Los datos fueron enviado al privado por exceso de caracteres no permitida por discord, cantidad maxima de `2000` caracteres.', ephemeral=True)
            await interaction.user.send(f'# consulta exitosa de usuarios. \n {respon[:1900]}')
            if len(json.dumps(respon, ensure_ascii=False, indent=2)) > 1900:
                await interaction.user.send(f'{respon[1900:3800]}')

@bot.tree.command(name='set_register', description='Envía el ui de registro para ingreso de jornada de trabajo.')
@commands.has_permissions(administrator=True, manage_guild=True)
async def set_register(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("No tienes permisos para usar este comando.", ephemeral=True)
        return
    embed = discord.Embed(
        title='Registro de Jornada Laboral.',
        color=10181046,
        description='¡Bienvenidos al sistema de registro de jornada laboral! Aquí podrás registrar tu tiempo de trabajo diario de manera rápida y sencilla. Es importante que cumplas con un mínimo de 2 horas de trabajo diarias, las cuales serán medidas a partir de tu estado en línea. El bot monitoreará tu actividad y calculará el tiempo que estés en línea, lo que determinará el tiempo total trabajado durante el día.\n\nPara comenzar tu jornada laboral, simplemente haz clic en el botón Registrar ingreso. Este botón marcará el inicio de tu trabajo. Cuando finalices tu jornada, no olvides hacer clic en el botón Registrar salida para que el bot registre el tiempo trabajado. Asegúrate de estar en línea durante el tiempo que deseas que se contabilice, ya que el bot solo cuenta el tiempo en el que apareces como conectado.'
    )
    message = await interaction.channel.send(embed=embed, view=ui.REGISTER(user_online, db))
    await interaction.response.send_message('**Canal seteado correctamente.**', ephemeral=True)
    # TODO: Guardamos el registro del mensaje enviado en la base de datos


@bot.tree.command(name='set_rol', description='Setea el Rol donde se registran los usuarios.')
@commands.has_permissions(administrator=True, manage_guild=True)
@app_commands.describe(rol='Rol para registrar el usuario')
@app_commands.autocomplete(rol=utils.autocomplete_roles)
async def set_rol(interaction: discord.Interaction, rol: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("No tienes permisos para usar este comando.", ephemeral=True)
        return
    server = interaction.guild
    try:
        role_obj = await utils.transform(interaction, rol)
        # TODO: Guardamos el rol seteado
        db.insertar("INSERT INTO roles (id_rol, rol_name, id_server, server_name) VALUES (%s, %s, %s, %s)", (role_obj.id, role_obj.name, server.id, server.name))
        role = discord.utils.get(server.roles, id=role_obj.id) # Obtenemos el rol con el id
        if role: # Verificamos si el rol existe
            for menber in role.members: # Iteramos los miembros del rol
                user_register[menber.id] = {'estado': ConverStatus(menber.status), 'name': menber.display_name}
                # TODO: Guardamos el los usuarios elegidos para el rol elegido
                db.insertar("INSERT INTO users (id, name, time) VALUES (%s, %s, %s)", (menber.id, menber.display_name, 0))
        em = ui.CreateEmbed('Seteo del rol Exitos', f'Se seteo el rol {role_obj.name} para {server.name} ({server.id})', color=ColorDiscord.GREEN.value)
        await interaction.response.send_message(embed=em, ephemeral=True)
    except Exception as e:
        em = ui.CreateEmbed('Seteo del rol Fallido', f'No se pudo setear el rol {rol} para {server.name} ({server.id})', color=ColorDiscord.RED.value)
        await interaction.response.send_message(embed=em, ephemeral=True)


@bot.tree.command(name='del_rol', description='Elimina el Rol donde se registran los usuarios.')
@commands.has_permissions(administrator=True, manage_guild=True)
@app_commands.describe(rol='Debes colocar solo el ID del rol a eliminar')
async def del_rol(interaction: discord.Interaction, rol: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("No tienes permisos para usar este comando.", ephemeral=True)
        return
    server = interaction.guild
    try:
        # TODO: Eliminamos el rol seleccionado en el comando.
        result = db.insertar("DELETE FROM roles WHERE id_rol = %s", (int(rol),))
        if result:
            await interaction.response.send_message(f'# Se elimino el rol {rol} para {server.name} ({server.id})', ephemeral=True)
        else:
            await interaction.response.send_message(f'# No se elimino el rol {rol} para {server.name} ({server.id})\n- El rol no se encuentra registrada.', ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f'# Error al eliminar el rol. \n{e}', ephemeral=True)


@bot.tree.command(name='get_roles', description='Obtiene la lista de roles registrados.')
@commands.has_permissions(administrator=True, manage_guild=True)
async def get_roles(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("No tienes permisos para usar este comando.", ephemeral=True)
        return
    # TODO: Consultamos los roles de la base de datos.
    data = db.consulta("SELECT * FROM roles").fetchall()
    respon = ''
    for i in data:
        respon += f'- Rol: {i[1]}, ID: {i[0]}, Servidor: {i[3]}\n'
    await interaction.response.send_message(f'# Consulta exitosa. \n{respon}', ephemeral=True)

@bot.tree.command(name='get_raw', description='Muestra los datos en raw de los usuarios registrados.')
@commands.has_permissions(administrator=True, manage_guild=True)
async def get_raw(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("No tienes permisos para usar este comando.", ephemeral=True)
        return
    if len(json.dumps(user_register, ensure_ascii=False, indent=2)) <= 1900:
        await interaction.response.send_message(f'# Consulta exitosa. \n```json\n{user_register}```', ephemeral=True)
    else:
        await interaction.response.send_message(f'# Consulta fallida. \n- Discord no permite enviar mas de 2000 caracteres.\n- Cantidad de caracteres de tu consulta: `{len(json.dumps(user_register, ensure_ascii=False, indent=2))}`', ephemeral=True)

@bot.tree.command(name='del_channel', description='Elimina el canal.')
@commands.has_permissions(administrator=True, manage_guild=True)
async def del_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("No tienes permisos para usar este comando.", ephemeral=True)
        return
    try:
        await interaction.response.send_message(f'# Se elimino el canal {channel.name} ({channel.id})', ephemeral=True)
        await channel.delete()
    except Exception as e:
        await interaction.response.send_message(f'# Error al eliminar el canal. \n{channel.name}', ephemeral=True)

@bot.tree.command(name='embed', description='Comando para crear Embed')
@commands.has_permissions(administrator=True)
@app_commands.autocomplete(color=utils.color_autocomplete)
@app_commands.describe(color='Color del Embed', title='Tiulo del Embed', description='Descripción del Embed', description_embed='Descripción del Embed', author='Autor del Embed', channel='Canal donde se enviara el Embed')
async def create_embed(interaction: discord.Interaction, channel: discord.TextChannel, color: str, title: typing.Optional[str] = None, description: typing.Optional[str] = None, description_embed: typing.Optional[str] = None, author: typing.Optional[discord.Member] = None):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("No tienes permisos para usar este comando.", ephemeral=True)
        return
    color_value = ColorDiscord[color.upper()].value
    description_embed = description_embed.replace('\\n', '\n')
    embed = discord.Embed(
        title=title,
        description=description_embed,
        color=color_value
    )

    if author is None and description is None:
        await channel.send(embed=embed)
        await interaction.response.send_message(f"Mensaje enviado al canal {channel.mention}", ephemeral=True)
    elif author is None:
        await channel.send(content=description,embed=embed)
        await interaction.response.send_message(f"Mensaje enviado al canal {channel.mention}", ephemeral=True)
    else:
        if description is None:
            embed.set_author(name=author.display_name, icon_url=author.display_avatar.url)
            await channel.send(embed=embed)
            await interaction.response.send_message(f"Mensaje enviado al canal {channel.mention}", ephemeral=True)
        else:
            await channel.send(f'{description}\n\nAutor: {author}',embed=embed)
            await interaction.response.send_message(f"Mensaje enviado al canal {channel.mention}", ephemeral=True)

# ? --------------------------- Sistema de tickets ---------------------------

@bot.tree.command(name='set_ticket', description='Setea el canal de tickets.')
@commands.has_permissions(administrator=True, manage_guild=True)
async def set_ticket(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("No tienes permisos para usar este comando.", ephemeral=True)
        return
    channel = interaction.channel
    embed = ui.CreateEmbed('Tickets', 'Aca puedes solicitar soporte para ayudar o reportar algun problema con **kailand**, la respuesta a tu ticket no sera de forma inmediata.\n\n> Solo puedes tener un ticket abierto por usuario.\n\n***Por favor, selecciona el tipo de soporte que necesitas:***', color=ColorDiscord.PURPLE.value)
    embed.set_thumbnail(url='https://raw.githubusercontent.com/GatoArtStudios/kailand_bot/Gatun/img/KLZ.gif')
    embed.set_footer(text='By Kailand', icon_url='https://raw.githubusercontent.com/GatoArtStudios/kailand_bot/Gatun/img/KLZ.gif')
    embed.set_image(url='https://raw.githubusercontent.com/GatoArtStudios/kailand_bot/Gatun/img/Banner_Tickets.png')

    view = ui.TicketSelectView()
    await interaction.response.send_message('Cargando...\nSeteando canal de tickets.', ephemeral=True)
    await channel.send(embed=embed, view=view)

@bot.tree.command(name='create_ticket', description='Crea un ticket personalizado para dar soporte a un usuario en concreto.')
@commands.has_permissions(administrator=True, manage_guild=True)
async def set_ticket(interaction: discord.Interaction, user: discord.Member):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("No tienes permisos para usar este comando.", ephemeral=True)
        return
    ticket = ui.CreateTicket(interaction, user)
    await ticket.create()

@bot.tree.command(name='set_server', description='Crea el embed para ver el estado del servidor de Minecraft.')
@commands.has_permissions(administrator=True, manage_guild=True)
async def set_server(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("No tienes permisos para usar este comando.", ephemeral=True)
        return
    tp = ui.StatusServerEmbed()
    embed = tp.onServer(timestamp)
    view = ui.ServerStatusView()
    await interaction.channel.send(embed=embed, view=view)
    await interaction.response.send_message('Embed del estado del servidor enviado.', ephemeral=True)

@bot.tree.command(name='ticket_priv', description='Vuelve el ticket privado.')
@commands.has_permissions(administrator=True, manage_guild=True)
@commands.has_permissions(manage_channels=True)
async def ticket_priv(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("No tienes permisos para usar este comando.", ephemeral=True)
        return
    channel = interaction.channel
    try:
        user = await utils.getUserTicket(interaction)
    except Exception as e:
        await interaction.response.send_message('Error al obtener el usuario autor del ticket.', ephemeral=True)
        return
    # Mueve el ticket a categoria privada
    target_category = discord.utils.get(interaction.guild.categories, id=TICKET_CATEGORY_PRIVATE_ID)
    guild = interaction.guild
    overwrites = {
        discord.utils.get(guild.roles, id=ID_ROLE_HELPER): discord.PermissionOverwrite(read_messages=False), # Le quita permisos de leer mensajes a helpers
        discord.utils.get(guild.roles, id=ID_ROLE_MOD): discord.PermissionOverwrite(read_messages=False), # Le quita permisos de leer mensajes a moderadores
        discord.utils.get(guild.roles, id=ID_ROLE_TECN): discord.PermissionOverwrite(read_messages=False), # Le quita permisos de leer mensajes a tecnicos
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True)
    }
    if not target_category:
        await interaction.response.send_message('No se encontro la categoria privada.', ephemeral=True)
        return
    # Mover el canal
    await channel.edit(category=target_category, overwrites=overwrites)
    await interaction.response.send_message('Ticket movido a la categoria privada.', ephemeral=True)

@bot.tree.command(name='ticket_import', description='Vuelve el ticket importante.')
@commands.has_permissions(administrator=True, manage_guild=True)
@commands.has_permissions(manage_channels=True)
async def ticket_import(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("No tienes permisos para usar este comando.", ephemeral=True)
        return
    channel = interaction.channel
    # Mueve el ticket a categoria importante
    target_category = discord.utils.get(interaction.guild.categories, id=TICKET_CATEGORY_IMPORT_ID)
    if not target_category:
        await interaction.response.send_message('No se encontro la categoria impontante.', ephemeral=True)
        return
    # Mover el canal
    await channel.edit(category=target_category)
    await interaction.response.send_message('Ticket movido a la categoria de importante.', ephemeral=True)

@bot.tree.command(name='ticket_mediun', description='Vuelve el ticket de importancia media.')
@commands.has_permissions(administrator=True, manage_guild=True)
@commands.has_permissions(manage_channels=True)
async def ticket_mediun(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("No tienes permisos para usar este comando.", ephemeral=True)
        return
    channel = interaction.channel
    # Mueve el ticket a categoria de importancia media
    target_category = discord.utils.get(interaction.guild.categories, id=TICKET_CATEGORY_MEDIUN_ID)
    if not target_category:
        await interaction.response.send_message('No se encontro la categoria importancia media.', ephemeral=True)
        return
    # Mover el canal
    await channel.edit(category=target_category)
    await interaction.response.send_message('Ticket movido a la categoria de importancia media.', ephemeral=True)

# ? --------------------------- De eventos loops ---------------------------


@tasks.loop(minutes=1.0)
async def event_loop_connection_db():
    '''
    Esta funcion se encargara de terminar la jornada laboral de un usuario si no lo hizo de forma manual.
    '''

    current_time = datetime.datetime.now()
    if current_time.hour == 0 and current_time.minute == 0:
        print('Es medianoche, reseteando user_online')

        for user_id in list(user_online.keys()):
            # buscamos que usuarios estan en modo 'EN_LINEA' y no han terminado su jornada laboral, y cambiamos a 'DESCONECTADO'
            if user_online[user_id]['estado'] == EstadosUsuario.EN_LINEA:
                # Luego lo almacenamos en la base de datos, luego le enviamos mensaje privado y por ultimo limpiamos el diccionario
                db.datetime(user_id, user_online[user_id]['name'], EstadosUsuario.DESCONECTADO)
                try:
                    user = await bot.fetch_user(user_id)
                    em = ui.CreateEmbed(title='Jornada laboral terminada', description=f'El usuario {user.mention} ha terminado su jornada laboral de forma automazada, recuerda que debes iniciar nuevamente tu jornada laboral.', color=ColorDiscord.BLUE.value)
                    await user.send(embed=em)
                except Exception as e:
                    logging.error(f'Error al enviar mensaje privado al usuario {user_id}, error: {e}')

        user_online.clear() # Limpiamos la lista de usuarios en jornada

@tasks.loop(seconds=5.0)
async def event_loop_check_server_status():
    try:
        global estado, timestamp
        status, players = await utils.StatusServer()
        if status == 'offline':
            if estado != 'Inactivo':
                timestamp = int(datetime.datetime.now().timestamp())
                if channel_status is not None:
                    ms = await channel_status.send('<@&1283242933298004091>')
                    await ms.delete()
            estado = 'Inactivo'
            if message_status_embed is not None:
                em = embed_status.offServer(timestamp, players)
                await message_status_embed.edit(embed=em)
        elif status == 'starting':
            if estado != 'Iniciando':
                timestamp = int(datetime.datetime.now().timestamp())
            estado == 'Iniciando'
            if message_status_embed is not None:
                em = embed_status.startingServer(timestamp, players)
                await message_status_embed.edit(embed=em)
        elif status == 'running':
            if estado != 'Activo':
                timestamp = int(datetime.datetime.now().timestamp())
                if channel_status is not None:
                    ms = await channel_status.send('<@&1283242933298004091>')
                    await ms.delete()
            estado = 'Activo'
            if message_status_embed is not None:
                em = embed_status.onServer(timestamp, players)
                await message_status_embed.edit(embed=em)
        elif status == 'stopping':
            if estado != 'Apagando':
                timestamp = int(datetime.datetime.now().timestamp())
            estado == 'Apagando'
            if message_status_embed is not None:
                em = embed_status.stoppingServer(timestamp, players)
                await message_status_embed.edit(embed=em)
        # print(estado)
        # print(channel_status)
    except Exception as e:
        print(e)

# ? --------------------------- Apartado de conexión del bot ---------------------------

def check_internet_connection():
    try:
        ping3.ping('discord.com', unit='ms')
        return True
    except:
        return False

# ? --------------------------- Iniciamos el bot y el loop de conexión ---------------------------
async def main():
    while True:
        if check_internet_connection():
            try:
                logging.info("Estableciendo conexión...")
                event_loop_connection_db.start()
                event_loop_check_server_status.start()
                await bot.start(config.TOKEN)
            except (socket.gaierror, aiohttp.client_exceptions.ClientConnectorError, RuntimeError):
                logging.error("Conexión cerrada por error de red.")
                event_loop_connection_db.stop()
                event_loop_check_server_status.stop()
                await bot.close()
                break
            except KeyboardInterrupt:
                logging.info("Cerrando...")
                await bot.close()
                break
        else:
            print('No internet connection. Retrying in 10 seconds...')
            await asyncio.sleep(10) # 10 time.sleep(10)

if __name__ == '__main__':
    asyncio.run(main())
