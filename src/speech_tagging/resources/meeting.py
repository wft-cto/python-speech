from flask_restful import Resource
from flask import request
from speech_tagging.models.meeting import MeetingModel
from speech_tagging.schemas.meeting import MeetingSchema
from speech_tagging.commons.utils import *
from speech_tagging.definitions import *
from speech_tagging.commons.messages import *

from speech_tagging.models.audio import AudioModel
from speech_tagging.commons import audio_helper

meeting_schema = MeetingSchema()


class Meeting(Resource):

    @classmethod
    def post(cls):
        """

        :param audio_link:
        :return:
        """
        meeting_json = request.get_json()
        # meeting_json = request.form
        if meeting_json is None:
            return {"message": "Invalid data"}, 400

        for key,value in meeting_json.items():
            # if key=="organization_id" or key=="total_attendee" or key=="audio_id":
            if value:
                pass
            else:
                return {"data": 
                                {},
                        "message":"This " + key + " field is required",
                        "success":False
                        }, 400

        try:
            audio_id = meeting_json.get("audio_id")
            audio_obj = AudioModel.query.get(audio_id)
            audio_filename = audio_helper.get_basename(audio_obj.path)
            print(audio_filename)
        except:
            return {"message":"audio id is required field"}
    

        if audio_filename is None:
            return {"message":"No audio_filename present"},400

        if meeting_json.get("transcription_filename") is None:
            print(audio_filename.split(".")[:-1])
            transcription_filename = ".".join(audio_filename.split(".")[:-1]) + ".json"
            meeting_json.update({"transcription_filename":transcription_filename})
            print(transcription_filename)
        else:
            # transcription_filename = meeting_json["transcription_filename"]
            transcription_filename = ".".join(audio_filename.split(".")[:-1]) + ".json"
            print("Else")

        meeting = meeting_schema.load(meeting_json)

        all_audio_files = get_all_filename_from_folder(MEETING_FOLDER)
        all_json_files = get_all_filename_from_folder(MEETING_FOLDER, PATH_JSON)

        if audio_filename not in all_audio_files:
            return {"message": AUDIO_DOES_NOT_EXIST.format(audio_filename)}, 400

        if transcription_filename not in all_json_files:
            return {"message": AUDIO_TRANSCRIPTION_DOESNOT_EXIST.format(transcription_filename), "result": "Not found it bro"}, 400

        if MeetingModel.find_by_audio_filename(audio_id):
            return {"message": "MEETING file already exists"}
            # return {"message": MEETING_ALREADY_EXISTS.format(audio_filename)}
        try:
            meeting.save_to_db()
        except:
            return {"message": ERROR_INSERTING}, 500

        return {"message":MEETING_CREATED_SUCCESSFULLY,
                "meeting":meeting_schema.dump(meeting)}, 201