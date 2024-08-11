import discord
from datetime import datetime
from types_utils import ColorDiscord
from discord.ui import Select, View, Button
import asyncio
import sql
from config import PATH as path
from config import TICKET_CATEGORY_ID, user_ticket
from types_utils import EstadosUsuario

db = sql.SQL()

# ? ------------------------------------ Views de los tickets (DropSelect) ------------------------------------

class TicketSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Soporte Minecraft", description="Ayuda con problemas con el servidor de minecraft.", emoji="🛠️"),
            discord.SelectOption(label="Soporte Discord", description="Ayuda con problemas con el servidor de discord.", emoji="💬"),
            discord.SelectOption(label="Soporte Launcher", description="Ayuda con problemas con el launcher.", emoji="🖥️"),
            discord.SelectOption(label="Reporte de Bugs", description="Informa sobre un error.", emoji="<:GC_anotao:812543341232259092>"),
        ]
        super().__init__(placeholder="Elige el tipo de soporte que necesitas.", custom_id="select", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        tipo_soporte = self.values[0].replace('Soporte ', '').replace('Consultas Generales', 'General').replace('Reporte de Bugs', 'Bugs')
        user = interaction.user
        guild = interaction.guild

        # Creamos el canal para el ticket
        category = discord.utils.get(guild.categories, id=TICKET_CATEGORY_ID)
        channel_name = f'{tipo_soporte}-{user.display_name}'.replace(' ', '-').lower()
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True),
            discord.utils.get(guild.roles, id=1154950225505550417): discord.PermissionOverwrite(read_messages=True), # Le da permisos de leer mensajes a helpers
            discord.utils.get(guild.roles, id=1105643863584014508): discord.PermissionOverwrite(read_messages=True), # Le da permisos de leer mensajes a moderadores
            discord.utils.get(guild.roles, id=1078126338638094366): discord.PermissionOverwrite(read_messages=True) # Le da permisos de leer mensajes a tecnicos
        }
        ticket_channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)

        await interaction.response.send_message(f'Ticket creado en {ticket_channel.mention}.', ephemeral=True)

        embed_ticket = CreateEmbed(
            f'Ticket de {tipo_soporte}',
            f'Bienvenido, {user.mention}.\nUn miembro del equipo de soporte te atenderá lo más rápido que puedan en el canal de tickets que acabas de crear.',
            color=ColorDiscord.GREEN.value
        )

        view = TicketCloseView()
        view_ticket = TicketSelectView()
        await interaction.message.edit(view=view_ticket)
        message = await ticket_channel.send(f'{user.mention}' ,embed=embed_ticket, view=view)
        user_ticket[ticket_channel.id] = user.id
        db.insertar('INSERT INTO ticket_messages (message_id, channel_id, author_id) VALUES (%s, %s, %s)', (message.id, ticket_channel.id, user.id))

# ? ------------------------------------ Views para los embeds que cierran los tickets ------------------------------------

class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketCloseButton())

class TicketCloseButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Cerra el ticket", emoji="🔒", custom_id="close_ticket", style=discord.ButtonStyle.red)

    async def callback(self, interaction: discord.Interaction):
        ticket_channel = interaction.channel
        if ticket_channel:
                try:
                    await interaction.response.send_message('Ticket cerrado.', ephemeral=True)
                    await asyncio.sleep(3)
                    await ticket_channel.delete()
                except Exception as e:
                    await interaction.response.send_message(f'Error al cerrar el ticket.', ephemeral=True)

# ? ------------------------------------ Clases de los embeds ------------------------------------

class CreateEmbed(discord.Embed):
    def __init__(self, title: str, description: str, color: int = 5763719):
        super().__init__(title=title, description=description, color=color)

class REGISTER(discord.ui.View):
    """
    Vista para el botón "Registrarse" que se muestra en el comando 'set_register'.
    """
    def __init__(self, user_online, db: sql.SQL):
        """
        Constructor de la clase.
        """
        super().__init__()
        self.db = db
        self.user_online = user_online

    @discord.ui.button(label="Registrar Ingreso", custom_id="register_button", style=discord.ButtonStyle.green)
    async def register_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Método asincrónico que se ejecuta cuando se hace click en el botón "Registrarse".
        """
        # Obtener la fecha y hora actual
        now = datetime.now()

        if interaction.user.id in self.user_online and self.user_online[interaction.user.id]['estado'] == EstadosUsuario.EN_LINEA:
            embed = CreateEmbed(title='Ya se encuentra registrada su entrada.', description='**Nota:** Por favor no spawnes el boto, ya te encuentras registrado como usuario en linea.')
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if interaction.user.id not in self.user_online:
            self.user_online[interaction.user.id] = {'estado': EstadosUsuario.EN_LINEA, 'name': interaction.user.display_name}
        else:
            self.user_online[interaction.user.id].update({'estado': EstadosUsuario.EN_LINEA, 'name': interaction.user.display_name})

        # Formatear la fecha y hora actual
        current_time_str = now.strftime('%Y-%m-%d %H:%M:%S')
        embed = discord.Embed(
            title="Su ingreso ha sido registrado existosamente a el dia: " + current_time_str + "",
            color=5763719,
            description='**Nota:** Recuerda registrar tu salida de la jornada laboral'
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        self.db.datetime(interaction.user.id, interaction.user.display_name, EstadosUsuario.EN_LINEA)
        embed = discord.Embed(
            title=f'Ticket de registro de ingreso el dia {current_time_str}',
            color=5763719,
            description='Si no ha sido usted, por favor ignore este mensaje.'
        )
        await interaction.user.send(embed=embed)
        view_buttons = REGISTER(user_online=self.user_online, db=self.db)
        await interaction.message.edit(view=view_buttons)

    @discord.ui.button(label='Registrar Salida', custom_id='register_out_button', style=discord.ButtonStyle.red)
    async def register_out_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Método asincrónico que se ejecuta cuando se hace click en el botón "Registrarse".
        """
        # Obtener la fecha y hora actual
        now = datetime.now()

        if interaction.user.id in self.user_online and self.user_online[interaction.user.id]['estado'] == EstadosUsuario.DESCONECTADO:
            embed = CreateEmbed('Registro Exitoso', 'Ya se encuentra registrada su salida.')
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if interaction.user.id not in self.user_online:
            self.user_online[interaction.user.id] = {'estado': EstadosUsuario.DESCONECTADO, 'name': interaction.user.display_name}
        else:
            self.user_online[interaction.user.id].update({'estado': EstadosUsuario.DESCONECTADO, 'name': interaction.user.display_name})

        # Formatear la fecha y hora actual
        current_time_str = now.strftime('%Y-%m-%d %H:%M:%S')
        em = CreateEmbed(title='Su salida ha sido registrada existosamente a el dia:' + current_time_str, description='Ten un grandioso dia.', color=15105570)
        await interaction.response.send_message(embed=em, ephemeral=True)
        self.db.datetime(interaction.user.id, interaction.user.display_name, EstadosUsuario.DESCONECTADO)
        em = CreateEmbed(f'Ticket de registro de salida el dia {current_time_str}.', color=15105570, description='Si no ha sido usted, por favor ignore este mensaje.')
        await interaction.user.send(embed=em)
        view_buttons = REGISTER(user_online=self.user_online, db=self.db)
        await interaction.message.edit(view=view_buttons)
