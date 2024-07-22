import sqlite3
from typing import Union
import types_utils
from datetime import datetime
import discord
from log import logging
from config import PATH

class SQL:
    def __init__(self):
        self.path = PATH
        self.conn = None
        self.cursor = None

    def connect(self):
        self.conn = sqlite3.connect(self.path)
        self.cursor = self.conn.cursor()

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.commit()
            self.conn.close()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def run(self, query):
        '''
        Ejecuta en la base de datos la query dada
        '''
        self.cursor.execute(query)

    def consulta(self, query):
        '''
        Ejecuta en la base de datos la query dada y devuelve el cursor
        '''
        self.cursor.execute(query)
        return self.cursor

    def insertar(self, query, values):
        '''
        Ejecuta en la base de datos la query dada e intenta insertar valores
        '''
        try:
            self.cursor.execute(query, values)
            return True
        except Exception as e:
            logging.error(f'Error al insertar query: {query}, error: {e}')
            return False

    def crear_tabla(self, query):
        '''
        Crea una nueva tabla en la base de datos
        '''
        self.cursor.execute(query)
        self.conn.commit()

    def datetime(self, user_id: int, user_name: str, estado: Union[types_utils.EstadosUsuario], timestamp: int = None):
        '''
        Crea un nuevo registro en la base de datos
        '''
        timestamp = int(datetime.now().timestamp())
        query = 'INSERT INTO datetime(user_id, user_name, timestamp, estado) VALUES(?, ?, ?, ?)'
        values = (user_id, user_name, timestamp, estado.value)
        print(f'{user_name} {estado.value}')
        self.insertar(query, values)

    def del_message(self, ctx: discord.Message, user_action: str, user_action_id: int):
        '''
        Registra los mensajes eliminados en el servidor de discord
        '''
        print('Registrando mensaje eliminado')
        timestamp = int(datetime.now().timestamp())
        query = 'INSERT INTO del_message (server, channel, message, message_author, message_author_id, user_action, user_action_id, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
        values = (ctx.guild.name, ctx.channel.name, ctx.content, ctx.author.name, ctx.author.id, user_action, user_action_id, timestamp)
        self.insertar(query, values)