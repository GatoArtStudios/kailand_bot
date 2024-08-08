import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ.get('TOKEN')
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
PUBLIC_KEY = os.environ.get('PUBLIC_KEY')
PATH = os.environ.get('PATH_DB')
API_URL = os.environ.get('API_URL')