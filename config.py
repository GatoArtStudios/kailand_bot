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