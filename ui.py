import discord
from datetime import datetime
import sql
from config import PATH as path
from types_utils import EstadosUsuario

class REGISTER(discord.ui.View):
    """
    Vista para el botón "Registrarse" que se muestra en el comando 'set_register'.
    """
    def __init__(self, user_online):
        """
        Constructor de la clase.
        """
        super().__init__()
        self.user_online = user_online

    @discord.ui.button(label="Registrar Ingreso", custom_id="register_button", style=discord.ButtonStyle.green)
    async def register_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Método asincrónico que se ejecuta cuando se hace click en el botón "Registrarse".
        """
        # Obtener la fecha y hora actual
        now = datetime.now()

        if interaction.user.id in self.user_online and self.user_online[interaction.user.id]['estado'] == EstadosUsuario.EN_LINEA:
            await interaction.response.send_message("Ya se encuentra registrada su entrada.", ephemeral=True)
            return

        if interaction.user.id not in self.user_online:
            self.user_online[interaction.user.id] = {'estado': EstadosUsuario.EN_LINEA, 'name': interaction.user.display_name}
        else:
            self.user_online[interaction.user.id].update({'estado': EstadosUsuario.EN_LINEA, 'name': interaction.user.display_name})

        # Formatear la fecha y hora actual
        current_time_str = now.strftime('%Y-%m-%d %H:%M:%S')
        await interaction.response.send_message("Su ingreso ha sido registrado existosamente a el dia: " + current_time_str + "", ephemeral=True)
        with sql.SQL() as db:
            db.datetime(interaction.user.id, interaction.user.display_name, EstadosUsuario.EN_LINEA)
        await interaction.user.send(f'## Ticket de registro de ingreso el dia {current_time_str}.\n\n- Si no ha sido usted, por favor ignore este mensaje.')

    @discord.ui.button(label='Registrar Salida', custom_id='register_out_button', style=discord.ButtonStyle.red)
    async def register_out_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Método asincrónico que se ejecuta cuando se hace click en el botón "Registrarse".
        """
        # Obtener la fecha y hora actual
        now = datetime.now()

        if interaction.user.id in self.user_online and self.user_online[interaction.user.id]['estado'] == EstadosUsuario.DESCONECTADO:
            await interaction.response.send_message("Ya se encuentra registrada su salida.", ephemeral=True)
            return

        if interaction.user.id not in self.user_online:
            self.user_online[interaction.user.id] = {'estado': EstadosUsuario.DESCONECTADO, 'name': interaction.user.display_name}
        else:
            self.user_online[interaction.user.id].update({'estado': EstadosUsuario.DESCONECTADO, 'name': interaction.user.display_name})

        # Formatear la fecha y hora actual
        current_time_str = now.strftime('%Y-%m-%d %H:%M:%S')
        await interaction.response.send_message("Su salida ha sido registrada existosamente a el dia: " + current_time_str + "", ephemeral=True)
        with sql.SQL() as db:
            db.datetime(interaction.user.id, interaction.user.display_name, EstadosUsuario.DESCONECTADO)
        await interaction.user.send(f'## Ticket de registro de salida el dia {current_time_str}.\n\n- Si no ha sido usted, por favor ignore este mensaje.')
