import os
from os.path import join, dirname
import json
import dotenv
from datetime import datetime
from requests.exceptions import ConnectionError

from flask import current_app as app

from ibm_watson import SpeechToTextV1

from speech_tagging.definitions import PATH_ENV,PATH_AUDIO
from speech_tagging.commons.audio_helper import get_extension
from speech_tagging.commons.messages import *
from speech_tagging.definitions import MEETING_FOLDER,MEETING_FOLDER_EDIT,PATH_JSON_MEETING,PATH_JSON_MEETING_EDIT
from speech_tagging.watson_speech.watson import Watson

dotenv.load_dotenv(PATH_ENV)


class WatsonSpeech(Watson):
    def __init__(self):
        super().__init__()

    def save_json(self,data,filename,request_method):
        """

        :param json:
        :param filename:
        :return:
        """
        filename = filename.split(".")[0]
        filename = ".".join((filename,"json"))
        filepath = os.path.join(PATH_JSON_MEETING,filename)
        
        # if request_method=="GET":
        #     print("get method save json")
        #     filepath = os.path.join(PATH_JSON_MEETING,filename)
        # elif request_method=="POST":
        #     print("post method save json")
        #     filepath = os.path.join(PATH_JSON_MEETING_EDIT,filename)
        with open(filepath, 'w') as f:
            json.dump(data, f)

    def transcribe_meeting(self,request_method,filename,language_customization_id):
        """

        :param filename:
        :return:
        """
        extension = get_extension(filename)
        filepath = os.path.join(PATH_AUDIO,MEETING_FOLDER,filename)
        content_type = "/".join(["audio",extension.split(".")[1]])

        app.logger.info(datetime.now())
        app.logger.info('get file detail')
        app.logger.info(extension)
        app.logger.info(content_type)
        app.logger.info("\n")


        try:
            with open(join(dirname(__file__), './.', filepath),
                           'rb') as audio_file:
                if language_customization_id == 'Default':
                    app.logger.info('get language customization id')
                    app.logger.info(language_customization_id)
                    try:
                        speech_recognition_results = self._speech_to_text.recognize(
                            audio=audio_file,
                            content_type=content_type,
                            speaker_labels=True,
                            smart_formatting=True,
                        ).get_result()
                        
                        print(speech_recognition_results)

                        app.logger.info('speech recognition result : \n')
                        app.logger.info(speech_recognition_results)
                        app.logger.info("\n")

                        # return speech_recognition_results,1

                    except Exception as e:
                        app.logger.info('Catch Exception: *************')
                        app.logger.info(str(e))
                        app.logger.info("\n")
                else:
                    speech_recognition_results = self._speech_to_text.recognize(
                        audio=audio_file,
                        content_type=content_type,
                        speaker_labels=True,
                        language_customization_id=language_customization_id,
                        smart_formatting=True,
                    ).get_result()

                    # return speech_recognition_results,1
            # self.save_json(speech_recognition_results,filename,request_method)
            
            app.logger.info(datetime.now())
            app.logger.info('finally after speech recognition result : \n')

            return speech_recognition_results,1

        except ConnectionError:
            app.logger.info(datetime.now())
            app.logger.info('Connection error \n')

            return CONNECTION_ERROR,0

        except Exception as Error:
            app.logger.info(datetime.now())
            app.logger.info('Exception error')
            app.logger.info(str(Error))
            app.logger.info("\n")

            return IBM_ERROR.format(Error.__str__()),0


if __name__ == "__main__":
    ws = WatsonSpeech()

    trascription  = ws.transcribe_meeting("GET","/home/bis/Downloads/Cut_phone_conversation.mp3","Default")
    print(trascription)