import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USER_DB_PATH = os.path.join(BASE_DIR, 'db', 'user.cfg')
IP_PORT = ('localhost', 8888)

# STATUS_CODES
AUTH_USER_NOT_EXIST = 501
AUTH_PASSWORD_NOT_CORRECT = 502
AUTH_USER_HAS_LOGIN = 503
AUTH_SUCCESS = 500
