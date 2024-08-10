import discord
from datetime import datetime
import sql
from config import PATH as path
from types_utils import EstadosUsuario

def CreateEmbed(title: str, description: str, color: int = 5763719):
    embed = discord.Embed(title=title, description=description, color=color)
    return embed

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
