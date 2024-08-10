import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Select, Button
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
from types_utils import EstadosUsuario, ConverStatus, ColorDiscord
from log import logging

# ? ------------------------------------ Configuracion de la base de datos ------------------------------------

db = SQL()

# TODO: Crea tablas en la base de datos
db.run("CREATE TABLE IF NOT EXISTS users (id BIGINT PRIMARY KEY, name VARCHAR(255), time BIGINT)")
db.run("CREATE TABLE IF NOT EXISTS message (id BIGINT PRIMARY KEY, channel BIGINT)")
db.run('CREATE TABLE IF NOT EXISTS channel (id BIGINT PRIMARY KEY, name VARCHAR(255), id_server BIGINT, server_name VARCHAR(255))')
db.run("CREATE TABLE IF NOT EXISTS roles (id_rol BIGINT PRIMARY KEY, rol_name VARCHAR(255), id_server BIGINT, server_name VARCHAR(255))")
db.run("CREATE TABLE IF NOT EXISTS datetime (id BIGINT AUTO_INCREMENT PRIMARY KEY, user_id BIGINT, user_name VARCHAR(255), timestamp BIGINT, estado VARCHAR(255))")
db.run("CREATE TABLE IF NOT EXISTS del_message (id BIGINT AUTO_INCREMENT PRIMARY KEY, server VARCHAR(255), channel VARCHAR(255), message VARCHAR(255), message_author VARCHAR(255), message_author_id BIGINT, user_action VARCHAR(255), user_action_id BIGINT, timestamp BIGINT)")
data = db.consulta("SELECT * FROM users").fetchall()


# ? ------------------------------------ Variables ------------------------------------

user_online = {}
user_register = {}
TICKET_CATEGORY_ID = 1196886668519677952


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
        message = db.consulta("SELECT * FROM message").fetchall()
        if len(message) > 0: # Verificamos si hay mensajes guardados
            logging.info(f'Editando el mensaje de registro con iD: {message[0][0]}')
            for i in message: # Iteramos los mensajes
                channel = bot.get_channel(i[1]) # Obtenemos el canal con el id
                if channel: # Verificamos si el canal existe
                    try:
                        message = await channel.fetch_message(i[0]) # Obtenemos el mensaje del canal con el id del mensaje
                        if message: # Verificamos si el mensaje existe
                            view = ui.REGISTER(user_online, db)
                            await message.edit(view=view) # Editamos el mensaje, esto nos permitirá seguir interactuando con el botón.
                    except Exception as e:
                        pass
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
                                db.insertar("INSERT INTO users (id, name, time) VALUES (%s, %s, %s)", (user_id, user_name, 0))
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
@commands.has_permissions(administrator=True)
async def info(interaction: discord.Interaction):
    await interaction.response.send_message(f'El bot se llama {bot.user.name} y su ID es {bot.user.id}', ephemeral=True)

@bot.tree.command(name='estadisticas', description='Muestra las estadísticas del los usuarios registrados')
async def update_state(interaction: discord.Interaction):
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
@commands.has_permissions(administrator=True)
async def insertar(interaction: discord.Interaction, usuario: discord.Member):
    # TODO: Guardamos en la base de datos el usuario elegido por el comando
    insert = db.insertar("INSERT INTO users (id, name, time) VALUES (%s, %s, %s)", (usuario.id, usuario.display_name, 0))
    if insert:
        await interaction.response.send_message(f'# Registro exitoso. \nInsertado {usuario.display_name} ({usuario.id})', ephemeral=True)
    else:
        await interaction.response.send_message(f'# Registro fallido. \nNo se inserto {usuario.display_name} ({usuario.id}), el usuario puede estar ya registrado.', ephemeral=True)

@bot.tree.command(name='borrar', description='Borra un usuario de la base de datos')
@commands.has_permissions(administrator=True)
async def borrar(interaction: discord.Interaction, usuario: discord.Member):
    # TODO: Eliminamos un usuario elegido de la base de datos
    del_user = db.insertar("DELETE FROM users WHERE id = %s", (usuario.id,))
    if del_user:
        await interaction.response.send_message(f'# Usuario borrado. \nBorrado {usuario.display_name} ({usuario.id})', ephemeral=True)
    else:
        await interaction.response.send_message(f'# Error al eliminar. \nNo se borro {usuario.display_name} ({usuario.id}), el usuario no existe.', ephemeral=True)

@bot.tree.command(name='get_users', description='Muestra los usuarios de la base de datos.')
@commands.has_permissions(administrator=True)
async def consulta(interaction: discord.Interaction):
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
@commands.has_permissions(administrator=True)
async def set_register(interaction: discord.Interaction):
    embed = discord.Embed(
        title='Registro de Jornada Laboral.',
        color=10181046,
        description='¡Bienvenidos al sistema de registro de jornada laboral! Aquí podrás registrar tu tiempo de trabajo diario de manera rápida y sencilla. Es importante que cumplas con un mínimo de 2 horas de trabajo diarias, las cuales serán medidas a partir de tu estado en línea. El bot monitoreará tu actividad y calculará el tiempo que estés en línea, lo que determinará el tiempo total trabajado durante el día.\n\nPara comenzar tu jornada laboral, simplemente haz clic en el botón Registrar ingreso. Este botón marcará el inicio de tu trabajo. Cuando finalices tu jornada, no olvides hacer clic en el botón Registrar salida para que el bot registre el tiempo trabajado. Asegúrate de estar en línea durante el tiempo que deseas que se contabilice, ya que el bot solo cuenta el tiempo en el que apareces como conectado.'
    )
    message = await interaction.channel.send(embed=embed, view=ui.REGISTER(user_online, db))
    await interaction.response.send_message('**Canal seteado correctamente.**', ephemeral=True)
    # TODO: Guardamos el registro del mensaje enviado en la base de datos
    db.insertar("INSERT INTO message (id, channel) VALUES (%s, %s)", (message.id, interaction.channel.id))


@bot.tree.command(name='set_rol', description='Setea el Rol donde se registran los usuarios.')
@commands.has_permissions(administrator=True)
@app_commands.describe(rol='Rol para registrar el usuario')
@app_commands.autocomplete(rol=utils.autocomplete_roles)
async def set_server(interaction: discord.Interaction, rol: str):
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
@commands.has_permissions(administrator=True)
@app_commands.describe(rol='Debes colocar solo el ID del rol a eliminar')
async def del_rol(interaction: discord.Interaction, rol: str):
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
@commands.has_permissions(administrator=True)
async def get_roles(interaction: discord.Interaction):
    # TODO: Consultamos los roles de la base de datos.
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

@bot.tree.command(name='del_channel', description='Elimina el canal.')
@commands.has_permissions(administrator=True)
async def del_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    try:
        await channel.delete()
        await interaction.response.send_message(f'# Se elimino el canal {channel.name} ({channel.id})', ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f'# Error al eliminar el canal. \n{channel.name}', ephemeral=True)


# ? --------------------------- Sistema de tickets ---------------------------

@bot.tree.command(name='set_ticket', description='Setea el canal de tickets.')
@commands.has_permissions(administrator=True)
# async def set_ticket(interaction: discord.Interaction, canal: discord.TextChannel):
async def set_ticket(interaction: discord.Interaction):
    embed = ui.CreateEmbed('Tickets', 'Aca puedes solicitar soporte para ayudar o reportar algun problema con **kailand**, la respuesta a tu ticket no sera de forma inmediata.\n\n> Solo puedes tener un ticket abierto por usuario.\n\n***Por favor, selecciona el tipo de soporte que necesitas:***', color=ColorDiscord.PURPLE.value)
    embed.set_thumbnail(url='https://raw.githubusercontent.com/GatoArtStudios/kailand_bot/Gatun/Banner_Tickets.png')
    # embed.set_footer(text='Creado por GatoArtStudios', icon_url='https://raw.githubusercontent.com/GatoArtStudios/kailand_bot/Gatun/Banner_Tickets.png')
    embed.set_image(url='https://raw.githubusercontent.com/GatoArtStudios/kailand_bot/Gatun/Banner_Tickets.png')
    options = [
        discord.SelectOption(label="Soporte Minecraft", description="Ayuda con problemas con el servidor de minecraft.", emoji="🛠️"),
        discord.SelectOption(label="Soporte Discord", description="Ayuda con problemas con el servidor de discord.", emoji="💬"),
        discord.SelectOption(label="Soporte Launcher", description="Ayuda con problemas con el launcher.", emoji="🖥️"),
        discord.SelectOption(label="Soporte Técnico", description="Ayuda con problemas técnicos.", emoji="👨‍💻"),
        discord.SelectOption(label="Consultas Generales", description="Resuelve tus dudas.", emoji="❓"),
        discord.SelectOption(label="Reporte de Bugs", description="Informa sobre un error.", emoji="🐛"),
    ]
    select = Select(
        placeholder='Elige el tipo de soporte que necesitas',
        options=options,
        custom_id='select',
        min_values=1,
        max_values=1
    )

    async def select_callback(interaction: discord.Interaction):
        tipo_soporte = select.values[0].replace('Soporte ', '').replace('Consultas Generales', 'General').replace('Reporte de Bugs', 'Bugs')
        user = interaction.user
        guild = interaction.guild

        # Creamos el canal para el ticket
        category = discord.utils.get(guild.categories, id=TICKET_CATEGORY_ID)
        channel_name = f'{tipo_soporte}-{user.display_name}'.replace(' ', '-').lower()
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True)
        }
        ticket_channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)

        await interaction.response.send_message(f'Ticket creado en {ticket_channel.mention}.', ephemeral=True)

        embed_ticket = ui.CreateEmbed(
            f'Ticket de {tipo_soporte}',
            f'Bienvenido, {user.mention}.\nUn miembro del equipo de soporte te atenderá lo más rápido que puedan en el canal de tickets que acabas de crear.',
            color=ColorDiscord.GREEN.value
        )
        close_buttom = Button(
            label='Cerra el ticket',
            emoji='🔒',
            custom_id='close_ticket',
            style=discord.ButtonStyle.red
        )
        async def close_buttom_callback(interaction: discord.Interaction):
            await ticket_channel.delete()
            await interaction.response.send_message('Ticket cerrado.', ephemeral=True)
        
        close_buttom.callback = close_buttom_callback
        
        view = View()
        view.add_item(close_buttom)
        
        await ticket_channel.send(f'{user.mention}' ,embed=embed_ticket, view=view)
    
    select.callback = select_callback
    view = View()
    view.add_item(select)
    await interaction.response.send_message(embed=embed, view=view)

# ? --------------------------- De eventos loops ---------------------------




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
            except (socket.gaierror, aiohttp.client_exceptions.ClientConnectorError, RuntimeError):
                logging.error("Conexión cerrada por error de red.")
                bot.close()
                break
            except KeyboardInterrupt:
                logging.info("Cerrando...")
                bot.close()
                break
        else:
            print('No internet connection. Retrying in 10 seconds...')
            time.sleep(10)