import mysql.connector
from mysql.connector import Error
from typing import Union
import types_utils
from datetime import datetime
import discord
import pandas as pd
from log import logging
import config

class SQL:
    def __init__(self):
        self.path = config.PATH
        self.conn = None
        self.cursor = None
        self.connect()

    def connect(self):
        try:
            if not self.conn or not self.conn.is_connected():
                self.conn = mysql.connector.connect(
                    host=config.DB_HOST,
                    user=config.DB_USER,
                    password=config.DB_PASSWD,
                    database=config.DB_NAME,
                    port=config.DB_PORT
                )
                self.cursor = self.conn.cursor()
                print(f'Conectado con la base de datos: {config.DB_NAME}')
        except Error as e:
            logging.error(f'Error al conectar con la base de datos: {e}')
            raise

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn and self.conn.is_connected():
            self.conn.close()
            print('Conexión con la base de datos cerrada.')

    def reconnect_if_needed(self):
        if not self.conn.is_connected():
            print('Reconectando con la base de datos...')
            self.connect()

    def run(self, query):
        '''
        Ejecuta en la base de datos la query dada
        '''
        try:
            self.reconnect_if_needed()
            self.cursor.execute(query)
            print(self.cursor.lastrowid)
            self.conn.commit()
        except Exception as e:
            logging.error(f'Error al ejecutar query: {query}, error: {e}')
            print(f'Error al ejecutar query: {query}, error: {e}')

    def consulta(self, query):
        '''
        Ejecuta en la base de datos la query dada y devuelve el cursor
        '''
        self.reconnect_if_needed()
        self.cursor.execute(query)
        print(self.cursor.lastrowid)
        # self.conn.commit()
        print(f'Consulta realizada: {query}')
        return self.cursor

    def insertar(self, query, values):
        '''
        Ejecuta en la base de datos la query dada e intenta insertar valores
        '''
        try:
            self.reconnect_if_needed()
            self.cursor.execute(query, values)
            print(self.cursor.lastrowid)
            self.conn.commit()
            print(f'Insertado query: {query}, values: {values}')
            return True
        except Exception as e:
            logging.error(f'Error al insertar query: {query}, error: {e}')
            print(f'Error al insertar query: {query}, error: {e}')
            return False

    def crear_tabla(self, query):
        '''
        Crea una nueva tabla en la base de datos
        '''
        self.reconnect_if_needed()
        self.cursor.execute(query)

    def datetime(self, user_id: int, user_name: str, estado: Union[types_utils.EstadosUsuario], timestamp: int = None):
        '''
        Crea un nuevo registro en la base de datos
        '''
        timestamp = int(datetime.now().timestamp())
        query = 'INSERT INTO datetime (user_id, user_name, timestamp, estado) VALUES (%s, %s, %s, %s)'
        values = (user_id, user_name, timestamp, estado.value)
        print(f'{user_name} {estado.value}')
        self.insertar(query, values)

    def del_message(self, ctx: discord.Message, user_action: str, user_action_id: int):
        '''
        Registra los mensajes eliminados en el servidor de discord
        '''
        print('Registrando mensaje eliminado')
        timestamp = int(datetime.now().timestamp())
        query = 'INSERT INTO del_message (server, channel, message, message_author, message_author_id, user_action, user_action_id, timestamp) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'
        values = (ctx.guild.name, ctx.channel.name, ctx.content, ctx.author.name, ctx.author.id, user_action, user_action_id, timestamp)
        self.insertar(query, values)

    def get_user_statistics(self):
        query = 'SELECT * FROM datetime'
        rows = self.consulta(query).fetchall()

        def timestamp_to_datetime(timestamp):
            return datetime.fromtimestamp(timestamp)

        df = pd.DataFrame(rows, columns=['id', 'user_id', 'user_name', 'timestamp', 'estado'])
        df['timestamp'] = df['timestamp'].apply(timestamp_to_datetime)
        print(df)
        # return rows
