import os
import dotenv
from speech_tagging.definitions import PATH_ENV

dotenv.load_dotenv(PATH_ENV)

PRODUCTION_MODE = False

if PRODUCTION_MODE:
    DEBUG = False
    DB_URL = os.environ.get("REMOTE_HOST")
else:
    DEBUG = True
    DB_URL = os.environ.get("LOCAL_HOST")


