import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ.get('TOKEN')
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
PUBLIC_KEY = os.environ.get('PUBLIC_KEY')
PATH = os.environ.get('PATH_DB')
API_URL = os.environ.get('API_URL')
DB_NAME = os.environ.get('DB_NAME')
DB_PASSWD = os.environ.get('DB_PASSWD')
DB_USER = os.environ.get('DB_USER')
DB_PORT = os.environ.get('DB_PORT')
DB_HOST = os.environ.get('DB_HOST')
ID_DEVELOPER = int(os.environ.get('ID_DEVELOPER'))
ID_ROLE_HELPER = int(os.environ.get('ID_ROLE_HELPER'))
TICKET_CATEGORY_ID = int(os.environ.get('TICKET_CATEGORY_ID'))
ID_ROLE_MOD = int(os.environ.get('ID_ROLE_MOD'))
ID_ROLE_TECN = int(os.environ.get('ID_ROLE_TECN'))
TICKET_CATEGORY_PRIVATE_ID = int(os.environ.get('TICKET_CATEGORY_PRIVATE_ID'))
TICKET_CATEGORY_MEDIUN_ID = int(os.environ.get('TICKET_CATEGORY_MEDIUN_ID'))
TICKET_CATEGORY_IMPORT_ID = int(os.environ.get('TICKET_CATEGORY_IMPORT_ID'))
ID_ROLE_SERVERSTATUS = int(os.environ.get('ID_ROLE_SERVERSTATUS'))
API_KEY = os.environ.get('API_KEY')
END_POINT_API = os.environ.get('END_POINT_API')
END_POINT_API_PLAYERS = os.environ.get('END_POINT_API_PLAYERS')
CHANNEL_STATUS_ID = int(os.environ.get('CHANNEL_STATUS_ID'))
MESSAGE_STATUS_ID = int(os.environ.get('MESSAGE_STATUS_ID'))

# Almacenamos los usaurios que han abierto tickets
user_ticket = {}