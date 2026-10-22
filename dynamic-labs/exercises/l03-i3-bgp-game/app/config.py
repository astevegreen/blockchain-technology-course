import os
from dotenv import load_dotenv


load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
    SOCKETIO_ASYNC_MODE = "eventlet"
    ROOM_ID_PREFIX = "BGP"
