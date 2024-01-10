from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson import SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import BasicAuthenticator
from speech_tagging.definitions import PATH_ENV
import os
import dotenv

dotenv.load_dotenv(PATH_ENV)


class Watson:
    def __init__(self):
        authenticator = IAMAuthenticator(os.environ["WATSON_KEY"])

        self._speech_to_text = SpeechToTextV1(
            authenticator=authenticator
        )
        self._speech_to_text.set_service_url(os.environ["WATSON_URL"])