import os
import traceback
import time

from sqlalchemy import asc, desc

from flask import current_app as app
from flask_restful import Resource
from flask_uploads import UploadNotAllowed
from flask import send_file, request,send_from_directory, url_for, jsonify

from speech_tagging.commons import audio_helper
from speech_tagging.commons.messages import *
from speech_tagging.commons.utils import get_all_filename_from_folder
from speech_tagging.definitions import MEETING_FOLDER
from speech_tagging.models.audio import AudioModel
from speech_tagging.models.organization import OrganizationModel
from speech_tagging.models.user_registration import User

# from app import token_required

from speech_tagging.models.audio import AudioModel
from speech_tagging.schemas.audio import AudioSchema
from speech_tagging.schemas.audio import AudioModelSchema

from speech_tagging.watson_speech import json_helper
from speech_tagging.commons.utils import get_all_jsonfile_from_folder
from speech_tagging.definitions import *


audio_schema = AudioSchema()
audio_model_schema = AudioModelSchema()
audios_model_schema = AudioModelSchema(many=True)


class MeetingAudioUpload(Resource):

    def post(self):
        """
        This endpoint is used to upload an audio file. It uses the
        JWT to retrieve user information and save the audio in the user's folder.
        If a file with the same name exists in the user's folder, name conflicts
        will be automatically resolved by appending a underscore and a smallest
        unused integer. (eg. filename.png to filename_1.png).
        """
        data = audio_schema.load(request.files)

        print(data)

        try:
            # Check if file with same name exist or not
            filename = data["audio"].filename
            all_audio_files = get_all_filename_from_folder(MEETING_FOLDER)

            if filename in all_audio_files:
                return {"message":AUDIO_ALREADY_EXISTS.format(filename)}, 400

            # save(self, storage, folder=None, name=None)
            audio_path = audio_helper.save_audio(data["audio"], folder=MEETING_FOLDER)
            # here we only return the basename of the audio and hide the internal folder structure from our user
            basename = audio_helper.get_basename(audio_path)
            return {"message": AUDIO_UPLOADED.format(basename),
                    "filename":basename}, 201

        except UploadNotAllowed:  # forbidden file type
            extension = audio_helper.get_extension(data["audio"])
            return {"message": AUDIO_ILLEGAL_EXTENSION.format(extension)}, 400

    def put(self):
        """

        :return:
        """
        data = audio_schema.load(request.files)
        try:
            # save(self, storage, folder=None, name=None)
            audio_path = audio_helper.save_audio(data["audio"], folder=MEETING_FOLDER)
            # here we only return the basename of the audio and hide the internal folder structure from our user
            basename = audio_helper.get_basename(audio_path)
            return {"message": AUDIO_UPLOADED.format(basename)}, 201
        except UploadNotAllowed:  # forbidden file type
            extension = audio_helper.get_extension(data["audio"])
            return {"message": AUDIO_ILLEGAL_EXTENSION.format(extension)}, 400


class MeetingAudios(Resource):
    def get(self):
        """
        Get path for all meeting audios
        :return:
        """
        filenames = get_all_filename_from_folder(MEETING_FOLDER)
        return {"data": filenames}, 200


class MeetingAudio(Resource):
    def get(self, audio_id: int):
        """
        This endpoint returns the requested audio if exists. It will use JWT to
        retrieve user information and look for the audio inside the user's folder.
        """
        # check if filename is URL secure
        audio_obj = AudioModel.find_by_id(audio_id)
        if audio_obj is None:
            return {
                    "message":"Audio file not found"
                    }, 404
            
        filename = os.path.basename(audio_obj.path)
        # print(filename)
        if not audio_helper.is_filename_safe(filename):
            return {"message": AUDIO_ILLEGAL_FILENAME.format(filename)}, 400
        try:
            # try to send the requested file to the user with status code 200
            # return send_file(audio_helper.get_path(filename, folder=MEETING_FOLDER))

            if filename not in get_all_filename_from_folder(MEETING_FOLDER):
                return {"message":AUDIO_DOES_NOT_EXIST.format(filename)}

            filename = os.path.join("audios/meeting_audio_files", filename)
            return {"audio_url":url_for('static', filename=filename, _external=False)}, 200
            # return send_file(audio_helper.get_path(filename, folder=MEETING_FOLDER))

        except FileNotFoundError:
            return {"message": AUDIO_NOT_FOUND.format(filename)}, 404

    def delete(self, audio_id: int):
        """
        This endpoint is used to delete the requested audio under the user's folder.
        It uses the JWT to retrieve user information.
        """

        print("HRE")
        audio_obj = AudioModel.find_by_id(audio_id)
        print(audio_obj)
        filename = audio_helper.get_basename(audio_obj.path)
        print(filename)
        audio_obj.delete_from_db()
        # check if filename is URL secure
        if not audio_helper.is_filename_safe(filename):
            return {"message": AUDIO_ILLEGAL_FILENAME.format(filename)}, 400

        try:
            os.remove(audio_helper.get_path(filename, folder=MEETING_FOLDER))
            return {"message": AUDIO_DELETED.format(filename)}, 200
        except FileNotFoundError:
            return {"message": AUDIO_NOT_FOUND.format(filename)}, 404
        except:
            traceback.print_exc()
            return {"message": AUDIO_DELETE_FAILED.format(filename)}, 500
        

class Audio(Resource):
    def get(self):
        url_data = request.args
        organization_id = int(url_data['organization_id'])
        
        # audios = AudioModel.query.filter_by(organization_id=organization_id).order_by(asc(AudioModel.filename))
        audios = AudioModel.query.filter_by(organization_id=organization_id).order_by(desc(AudioModel.created_date))
        print("Audios>>>>",audios)
        audios = audios_model_schema.dump(audios)
        # app.logger.info(type(audios))
        # app.logger.info(audios)
        # audio_list = audios[0]
        # app.logger.info(audio_list)
        for audio in audios:
            action_count = 0
            path = audio['path']
            filename = audio_helper.get_basename(path)
            basename = filename.split(".")[0]
            json_filename = ".".join((basename, "json"))

            all_json_files = get_all_jsonfile_from_folder(MEETING_FOLDER)
            if json_filename in all_json_files:
                json_filepath = os.path.join(PATH_JSON_MEETING,json_filename)
                transcript_data = json_helper.read_json(json_filepath)
                results = transcript_data["results"]
                
                for result in results:
                    # app.logger.info(len(result['action_phrase']))
                    action_count += len(result['action_phrase'])
            # app.logger.info(action_count)
            audio.update({'action_count':action_count})

        return {"audios":audios}       
    
    
    def post(self):
        other_data = request.form
        if other_data is None:
            return {"data": 
                            {},
                    "message":"Invalid data",
                    "success":"False"
                    }, 400
        
        for key,value in other_data.items():
            if key == "organization_id":
                if value:
                    organization_id = int(value)
                    organization = OrganizationModel.find_by_id(organization_id)
                    if organization is None: 
                        return {"data": 
                                        {},
                                "message":"Organization not found",
                                "success":"False"
                                }, 400
            if key == "user_id":
                if value:
                    user_id = int(value)
                    user = User.find_by_id(user_id)
                    if user is None: 
                        return {"data": 
                                        {},
                                "message":"User not found",
                                "success":"False"
                                }, 400
            if key =="filename":
                if value:
                    is_filename_exist = bool(AudioModel.query.filter_by(filename=value).first())
                    if is_filename_exist:
                        return {
                                "data": {},
                                "message":"Filename already exists",
                                "success":False
                                }, 400
            # check value in each field          
            if value:
                pass
            else:
                return {"data": 
                                {},
                        "message":"This " + key  + " is required field",
                        "success":"False"
                        }, 400

         
        audio_data = audio_schema.load(request.files)        
        try:
            # Check if file with same name exist or not
            filename = audio_data["audio"].filename
            print('here is fileName:===>',filename)
            app.logger.info("***************" * 5)
            app.logger.info(filename)
            app.logger.info("***************" * 5)
            extension = audio_helper.get_extension(audio_data["audio"])
            app.logger.info(extension)
            print("myfile extension",extension)
            if extension==".mp3" or extension==".wav" or extension==".aac" or extension==".m4a" or extension==".mp4":
                print("I am in If block")
                pass
            else:
                print("I am in else block")
                # return {"message": AUDIO_ILLEGAL_EXTENSION.format(extension)}, 400
                return {"data":
                                {},
                        "message": AUDIO_ILLEGAL_EXTENSION.format(extension),
                        "success":False
                        }, 400

            all_audio_files = get_all_filename_from_folder(MEETING_FOLDER)

            # if filename in all_audio_files:
            #     return {"message":AUDIO_ALREADY_EXISTS.format(filename)}, 400

            # save(self, storage, folder=None, name=None)

            # audio_path = audio_helper.save_audio(audio_data["audio"],name=str(time.strftime("%Y%m%d-%H%M%S")) + extension, folder=MEETING_FOLDER)
            audio_path = audio_helper.convert_and_save_audio(audio_data["audio"],name=str(time.strftime("%Y%m%d-%H%M%S") + extension), folder=MEETING_FOLDER)

            # here we only return the basename of the audio and hide the internal folder structure from our user
            basename = audio_helper.get_basename(audio_path)
            # return {"message": AUDIO_UPLOADED.format(basename),
            #         "filename":basename}, 201

        except UploadNotAllowed:  # forbidden file type
            extension = audio_helper.get_extension(audio_data["audio"])
            return {"message": AUDIO_ILLEGAL_EXTENSION.format(extension), "result": "we are here now"}, 400

        
        try:
            audio = AudioModel(filename=other_data['filename'],
                               path=audio_path,
                               organization_id=other_data['organization_id'],
                               user_id=other_data['user_id'],
                               date=other_data['date']
                               )
            audio.save_to_db()
        except Exception as e:
            print(e)
            return {"data":
                            {},
                    # "message": "Something goes wrong in server",
                    "message": str(e),
                    "success":False
                    }, 500

        return {"data":
                        {
                        "audio":audio_model_schema.dump(audio)
                        },
                "message":"Audio uploaded successfully",
                "success":True
                }, 201
        
        # return {"message":"just check"}