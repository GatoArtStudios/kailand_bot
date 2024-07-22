import discord
from discord.ext import commands
from discord import app_commands
import logging
import ping3
import time
import socket
import aiohttp
import json
import asyncio
import ui
from  sql import SQL
import utils
import config
from types_utils import EstadosUsuario, ConverStatus
from log import logging

# ? ------------------------------------ Configuracion de la base de datos ------------------------------------

# TODO: Crea tablas en la base de datos
with SQL() as db:
    db.run("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, time INTEGER)")
    db.run("CREATE TABLE IF NOT EXISTS user_activity (date INTEGER PRIMARY KEY, id INTEGER, time INTEGER, name TEXT)")
    db.run("CREATE TABLE IF NOT EXISTS message (id INTEGER PRIMARY KEY, channel INTEGER)")
    db.run("CREATE TABLE IF NOT EXISTS roles (id_rol INTEGER PRIMARY KEY, rol_name TEXT, id_server INTEGER, server_name TEXT)")
    db.run("CREATE TABLE IF NOT EXISTS datetime (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, user_name TEXT, timestamp INTEGER, estado TEXT)")
    db.run("CREATE TABLE IF NOT EXISTS del_message (id INTEGER PRIMARY KEY AUTOINCREMENT, server TEXT, channel TEXT, message TEXT, message_author TEXT, message_author_id INTEGER, user_action TEXT, user_action_id INTEGER, timestamp INTEGER)")
    data = db.consulta("SELECT * FROM users").fetchall()


# ? ------------------------------------ Variables ------------------------------------

user_online = {}
user_register = {}


# ? -------------------------------------- Configuracion de Discord --------------------------------------

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.presences = True
intents.members = True

bot = commands.Bot(command_prefix='/', intents=intents)

# ?------------------------------------ Eventos ------------------------------------

@bot.event
async def on_ready():
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
        # TODO: Consultamos todos los mensajes de la base de datos
        with SQL() as db:
            message = db.consulta("SELECT * FROM message").fetchall()
        if len(message) > 0: # Verificamos si hay mensajes guardados
            logging.info(f'Editando el mensaje de registro con iD: {message[0][0]}')
            for i in message: # Iteramos los mensajes
                channel = bot.get_channel(i[1]) # Obtenemos el canal con el id
                if channel: # Verificamos si el canal existe
                    try:
                        message = await channel.fetch_message(i[0]) # Obtenemos el mensaje del canal con el id del mensaje
                        if message: # Verificamos si el mensaje existe
                            view = ui.REGISTER(user_online)
                            await message.edit(view=view) # Editamos el mensaje, esto nos permitirá seguir interactuando con el botón.
                    except Exception as e:
                        pass
        # ? ------------------------------------ Buscamos los usuarios a monitoria la actividad ------------------------------------
        # TODO: Consultamos todos los roles de la base de datos
        with SQL() as db:
            server = db.consulta("SELECT * FROM roles").fetchall()
        if len(server) > 0: # Verificamos si hay roles guardados
            for i in server: # Iteramos los roles
                # print(i)
                server = bot.get_guild(i[2]) # Obtenemos el servidor con el id
                if server: # Verificamos si el servidor existe
                    role = discord.utils.get(server.roles, id=i[0]) # Obtenemos el rol con el id
                    if role: # Verificamos si el rol existe
                        for menber in role.members: # Iteramos los miembros del rol
                            user_id, user_name, status = menber.id, menber.display_name, menber.status
                            logging.info(f'Usuario registrado: {user_id}, {user_name}')
                            # continue
                            if user_id and user_name:
                                if user_id not in user_online and ConverStatus(status) == EstadosUsuario.EN_LINEA:
                                    user_online[user_id] = {'estado': ConverStatus(status), 'name': user_name}
                                if user_id not in user_register:
                                    user_register[user_id] = {'estado': ConverStatus(status), 'name': user_name}
                                else:
                                    user_register[user_id].update({'estado': ConverStatus(status), 'name': user_name})
                                # TODO: Guardamos el usuario en la base de datos
                                with SQL() as db:
                                    db.insertar("INSERT INTO users VALUES (?, ?, ?)", (user_id, user_name, 0))
                            else:
                                continue
    # ? ------------------------------------ Sincronizamos comandos y actualizamos el estado del bot ------------------------------------
        synced = await bot.tree.sync()
        logging.info(f'Sincronizando {len(synced)} commando (s)')
    except Exception as e:
        logging.error(f'Tipo de error {e}')
    # Responde al evento colocando el estado de la actividad personalizada
    await bot.change_presence(activity=presence)

# ? ------------------------------------ Evento de presencia ------------------------------------
@bot.event
async def on_presence_update(before: discord.Member, after: discord.Member):
    if after.id in user_register and after.id in user_online and after.status != before.status:

        if after.status == discord.Status.online and before.status != discord.Status.online and after.status != before.status:
            if user_online[after.id]['estado'] != EstadosUsuario.EN_LINEA:
                user_online[after.id] = {'estado': EstadosUsuario.EN_LINEA, 'name': after.display_name}
                # TODO: Guardamos el usuario en la base de datos
                with SQL() as db:
                    db.datetime(after.id, after.display_name, EstadosUsuario.EN_LINEA)
                logging.info(f'Estado: {EstadosUsuario.EN_LINEA}, {after.display_name}, ({after.id})')

        elif after.status == discord.Status.dnd and before.status != discord.Status.dnd  and after.status != before.status:
            if user_online[after.id]['estado'] != EstadosUsuario.NO_MOLESTAR:
                user_online[after.id] = {'estado': EstadosUsuario.NO_MOLESTAR, 'name': after.display_name}
                # TODO: Guardamos el usuario en la base de datos
                with SQL() as db:
                    db.datetime(after.id, after.display_name, EstadosUsuario.NO_MOLESTAR)
                logging.info(f'Estado: {EstadosUsuario.NO_MOLESTAR}, {after.display_name}, ({after.id})')

        elif after.status == discord.Status.idle and before.status != discord.Status.idle  and after.status != before.status:
            if user_online[after.id]['estado'] != EstadosUsuario.AUSENTE:
                user_online[after.id] = {'estado': EstadosUsuario.AUSENTE, 'name': after.display_name}
                # TODO: Guardamos el usuario en la base de datos
                with SQL() as db:
                    db.datetime(after.id, after.display_name, EstadosUsuario.AUSENTE)
                logging.info(f'Estado: {EstadosUsuario.AUSENTE}, {after.display_name}, ({after.id})')

        elif after.status == discord.Status.invisible and before.status != discord.Status.invisible  and after.status != before.status:
            if user_online[after.id]['estado'] != EstadosUsuario.DESCONECTADO:
                user_online[after.id] = {'estado': EstadosUsuario.DESCONECTADO, 'name': after.display_name}
                # TODO: Guardamos el usuario en la base de datos
                with SQL() as db:
                    db.datetime(after.id, after.display_name, EstadosUsuario.DESCONECTADO)
                logging.info(f'Estado: {EstadosUsuario.DESCONECTADO}, {after.display_name}, ({after.id})')

        elif after.status == discord.Status.offline and before.status != discord.Status.offline  and after.status != before.status:
            if user_online[after.id]['estado'] != EstadosUsuario.DESCONECTADO:
                user_online[after.id] = {'estado': EstadosUsuario.DESCONECTADO, 'name': after.display_name}
                # TODO: Guardamos el usuario en la base de datos
                with SQL() as db:
                    db.datetime(after.id, after.display_name, EstadosUsuario.DESCONECTADO)
                logging.info(f'Estado: {EstadosUsuario.DESCONECTADO}, {after.display_name}, ({after.id})')

# ? ------------------------------------ Eventos de mensajes ------------------------------------

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
            with SQL() as db:
                db.del_message(message, entry.user.display_name, entry.user.id)
            break


# ? -------------------------------------- Definición de comandos --------------------------------------

@bot.tree.command(name='info', description='Ver información del bot')
@commands.has_permissions(administrator=True)
async def info(interaction: discord.Interaction):
    await interaction.response.send_message(f'El bot se llama {bot.user.name} y su ID es {bot.user.id}', ephemeral=True)

@bot.tree.command(name='estadisticas', description='Muestra las estadísticas del los usuarios registrados')
async def update_state(interaction: discord.Interaction):
    await interaction.response.send_message(f'recopilando estadisticas, por favor espere', ephemeral=True)
    # TODO: Mostramos las estadísticas de los usuarios registrados
    with SQL() as db:
        stats = db.get_user_statistics()
    #     print(stats)
    # response = "# Estadísticas de tiempo en línea por día:\n"
    # for row in stats:
    #     horas = round(row[3])
    #     response += f"- Usuario: {row[1]} ({row[0]}), Día: {row[2]}, Horas en línea: {horas}\n"
    # await interaction.user.send(response)

@bot.tree.command(name='insertar', description='Inserta un nuevo usuario a la base de datos.')
@commands.has_permissions(administrator=True)
async def insertar(interaction: discord.Interaction, usuario: discord.Member):
    # TODO: Guardamos en la base de datos el usuario elegido por el comando
    with SQL() as db:
        insert = db.insertar("INSERT INTO users VALUES (?, ?, ?)", (usuario.id, usuario.display_name, 0))
    if insert:
        await interaction.response.send_message(f'# Registro exitoso. \nInsertado {usuario.display_name} ({usuario.id})', ephemeral=True)
    else:
        await interaction.response.send_message(f'# Registro fallido. \nNo se inserto {usuario.display_name} ({usuario.id}), el usuario puede estar ya registrado.', ephemeral=True)

@bot.tree.command(name='borrar', description='Borra un usuario de la base de datos')
@commands.has_permissions(administrator=True)
async def borrar(interaction: discord.Interaction, usuario: discord.Member):
    # TODO: Eliminamos un usuario elegido de la base de datos
    with SQL() as db:
        del_user = db.insertar("DELETE FROM users WHERE id = ?", (usuario.id,))
    if del_user:
        await interaction.response.send_message(f'# Usuario borrado. \nBorrado {usuario.display_name} ({usuario.id})', ephemeral=True)
    else:
        await interaction.response.send_message(f'# Error al eliminar. \nNo se borro {usuario.display_name} ({usuario.id}), el usuario no existe.', ephemeral=True)

@bot.tree.command(name='get_users', description='Muestra los usuarios de la base de datos.')
@commands.has_permissions(administrator=True)
async def consulta(interaction: discord.Interaction):
    # TODO: Obtenemos todos los usuarios registrados en la base de datos
    with SQL() as db:
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
@commands.has_permissions(administrator=True)
async def set_register(interaction: discord.Interaction):
    message = await interaction.channel.send('# Puedes registrar tu ingreso de jornada de trabajo. \n- Por favor presiona el botón para registrar tu ingreso a trabajar.', view=ui.REGISTER(user_online))
    # TODO: Guardamos el registro del mensaje enviado en la base de datos
    with SQL() as db:
        db.insertar("INSERT INTO message VALUES (?, ?)", (message.id, interaction.channel.id))


@bot.tree.command(name='set_rol', description='Setea el Rol donde se registran los usuarios.')
@commands.has_permissions(administrator=True)
@app_commands.describe(rol='Rol para registrar el usuario')
@app_commands.autocomplete(rol=utils.autocomplete_roles)
async def set_server(interaction: discord.Interaction, rol: str):
    server = interaction.guild
    try:
        role_obj = await utils.transform(interaction, rol)
        # TODO: Guardamos el rol seteado
        with SQL() as db:
            db.insertar("INSERT INTO roles VALUES (?, ?, ?, ?)", (role_obj.id, role_obj.name, server.id, server.name))
        role = discord.utils.get(server.roles, id=role_obj.id) # Obtenemos el rol con el id
        if role: # Verificamos si el rol existe
            for menber in role.members: # Iteramos los miembros del rol
                user_register[menber.id] = {'estado': ConverStatus(menber.status), 'name': menber.display_name}
                # TODO: Guardamos el los usuarios elegidos para el rol elegido
                with SQL() as db:
                    db.insertar("INSERT INTO users VALUES (?, ?, ?)", (menber.id, menber.display_name, 0))
        await interaction.response.send_message(f'# Se seteo el rol {role_obj.name} para {server.name} ({server.id})', ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f'# Error al setear el rol. \n{e}', ephemeral=True)


@bot.tree.command(name='del_rol', description='Elimina el Rol donde se registran los usuarios.')
@commands.has_permissions(administrator=True)
@app_commands.describe(rol='Debes colocar solo el ID del rol a eliminar')
async def del_rol(interaction: discord.Interaction, rol: str):
    server = interaction.guild
    try:
        # TODO: Eliminamos el rol seleccionado en el comando.
        with SQL() as db:
            result = db.insertar("DELETE FROM roles WHERE id_rol = ?", (int(rol),))
        if result:
            await interaction.response.send_message(f'# Se elimino el rol {rol} para {server.name} ({server.id})', ephemeral=True)
        else:
            await interaction.response.send_message(f'# No se elimino el rol {rol} para {server.name} ({server.id})\n- El rol no se encuentra registrada.', ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f'# Error al eliminar el rol. \n{e}', ephemeral=True)


@bot.tree.command(name='get_roles', description='Obtiene la lista de roles registrados.')
@commands.has_permissions(administrator=True)
async def get_roles(interaction: discord.Interaction):
    # TODO: Consultamos los roles de la base de datos.
    with SQL() as db:
        data = db.consulta("SELECT * FROM roles").fetchall()
    respon = ''
    for i in data:
        respon += f'- Rol: {i[1]}, ID: {i[0]}, Servidor: {i[3]}\n'
    await interaction.response.send_message(f'# Consulta exitosa. \n{respon}', ephemeral=True)

@bot.tree.command(name='get_raw', description='Muestra los datos en raw de los usuarios registrados.')
@commands.has_permissions(administrator=True)
async def get_raw(interaction: discord.Interaction):
    if len(json.dumps(user_register, ensure_ascii=False, indent=2)) <= 1900:
        await interaction.response.send_message(f'# Consulta exitosa. \n```json\n{user_register}```', ephemeral=True)
    else:
        await interaction.response.send_message(f'# Consulta fallida. \n- Discord no permite enviar mas de 2000 caracteres.\n- Cantidad de caracteres de tu consulta: `{len(json.dumps(user_register, ensure_ascii=False, indent=2))}`', ephemeral=True)


# ? --------------------------- Apartado de conexión del bot ---------------------------

def check_internet_connection():
    try:
        ping3.ping('discord.com', unit='ms')
        return True
    except:
        return False

# ? --------------------------- Iniciamos el bot y el loop de conexión ---------------------------
if __name__ == '__main__':
    while True:
        if check_internet_connection():
            try:
                logging.info("Estableciendo conexión...")
                bot.run(config.TOKEN)
                time.sleep(3)
            except (socket.gaierror, aiohttp.client_exceptions.ClientConnectorError, RuntimeError):
                logging.error("Conexión cerrada por error de red.")
            except KeyboardInterrupt:
                logging.info("Cerrando...")
                break
        else:
            print('No internet connection. Retrying in 10 seconds...')
            time.sleep(10)