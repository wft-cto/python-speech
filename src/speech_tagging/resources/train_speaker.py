import json

import os
import pickle
import werkzeug
import shutil
from flask import request

from speech_tagging.db import db

from speech_tagging.models.embedding import EmbeddingModel
from speech_tagging.models.attendee import AttendeeModel, attendee_audio
from speech_tagging.models.organization import OrganizationModel
from speech_tagging.models.audio import AudioModel
from speech_tagging.commons.messages import ATTENDEE_DOES_NOT_EXIST,TRAINING_SUCCESSFUL, TRAINING_FAILED
from speech_tagging.commons.recognition_helper import load_data, delete_embedding_for_user

from flask_restful import Resource,reqparse
from speech_tagging.speaker_recognition.manager import manager
from speech_tagging.definitions import PATH_ATTENDEE_VOICE_SAMPLE, PATH_EMBEDDING, PATH_JSON_MEETING_EDIT
from speech_tagging.commons.utils import get_all_filepaths, get_all_jsonfile_from_folder
from speech_tagging.commons.messages import *
from speech_tagging.commons import audio_helper
from speech_tagging.watson_speech import json_helper
from speech_tagging.definitions import *


# def replace_attendee_detail_by_unknown(transcript_data,attendee_id):
#     for key,value in transcript_data["recognized_speakers"].items():
#         if value == "Unknown":
#             pass
#         else:
#             if value["id"] == attendee_id:
#                 transcript_data["recognized_speakers"][key] = "Unknown"
#     return transcript_data

class DeleteAttendeeEmbeding(Resource):
    @classmethod
    def delete(cls, attendee_id):
        delete = delete_embedding_for_user(attendee_id)

        return delete


class TrainSpeaker(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('organization_id',
                        type=int,
                        required=True,
                        help='This field cannot be left blank!')
    parser.add_argument('audio_id',
                        type=int,
                        required=True,
                        help='This field cannot be blank!')
    parser.add_argument('attendee_id',
                        type=int,
                        required=True,
                        help='This field cannot be blank!')
    parser.add_argument('speaker_id',
                        type=str,
                        required=True,
                        help='This field cannot be blank!')
    parser.add_argument('start_time',
                        type=int,
                        required=False)
    parser.add_argument('end_time',
                        type=int,
                        required=False)

    @classmethod
    def post(cls):
        """
        :param attendee_id:
        :return:
        """
        cls.data = cls.parser.parse_args()

        organization_id = cls.data["organization_id"]
        audio_id = cls.data['audio_id']
        attendee_id = cls.data['attendee_id']
        speaker_id = cls.data['speaker_id']
        start_time = cls.data['start_time']
        end_time = cls.data['end_time']

        if OrganizationModel.find_by_id(organization_id) is None:
            return {
                       "data": {},
                       "success": False,
                       "message": ORGANIZATION_DOES_NOT_EXIST.format(organization_id)
                   }, 400

        audio = AudioModel.find_by_id(audio_id)

        if audio is None:
            return {
                       "data": {},
                       "success": False,
                       "message": AUDIO_DOES_NOT_EXIST.format(audio_id)
                   }, 400
        attendee = AttendeeModel.find_by_id(int(attendee_id))
        if attendee is None:
            return {
                       "data": {},
                       "success": False,
                       "message": ATTENDEE_DOES_NOT_EXIST.format(attendee_id)
                   }, 400

        # json_filepath = os.path.join(PATH_JSON_MEETING, meeting.transcription_filename)
        # speaker_chunk = json_helper.pipeline(json_filepath)
        #
        # audio_object, ext = audio_helper.create_audio_segment_object(meeting.audio_filename)
        # for chunk in speaker_chunk:
        #     audio_helper.trim_and_save_audio_from_chunk(audio_object, ext, chunk, meeting.audio_filename,
        #                                                 PATH_SPEAKER_RECOGNITION)

        # Saving audio files
        filename = audio_helper.get_basename(audio.path)

        basename = filename.split(".")[0]
        json_filename = ".".join((basename, "json"))
        json_filepath = os.path.join(PATH_JSON_MEETING, json_filename)
        
        # update recognized_speaker in audio json file 
        transcript_data = json_helper.read_json(json_filepath)
        # print(transcript_data["recognized_speakers"])
        for key,value in transcript_data["recognized_speakers"].items():
            # if key == str(speaker_id) and value == "Unknown":
            if key == str(speaker_id):
                    transcript_data["recognized_speakers"][key] = attendee.json()
                
        # print("my data==========>",transcript_data["recognized_speakers"])      
        with open(json_filepath,'w') as write_file:
            json.dump(transcript_data,write_file)
            
        
        speaker_chunk = json_helper.get_speaker_speak_time(speaker_id,json_filepath)
        print("speaker chuncks================>",speaker_chunk)

        chunk = {
            "from" : start_time,
            "to": end_time        }
    
        audio_object, ext = audio_helper.create_audio_segment_object(filename)
        # for chunk in speaker_chunk:
        audio_helper.trim_and_save_audio_from_chunk(audio_object,attendee_id, ext, chunk, filename,
                                                        PATH_ATTENDEE_VOICE_SAMPLE)


        voice_samples = get_all_filepaths(str(attendee_id),PATH_ATTENDEE_VOICE_SAMPLE)
        embedding_file = os.path.join(PATH_EMBEDDING,"embedding.pickle")

        if os.path.exists(embedding_file):
            if os.stat(embedding_file).st_size == 0:
                speaker = []
                speaker_embedding = []
            else:
                data = pickle.loads(open(embedding_file,"rb").read())
                speaker = data["speaker"]
                speaker_embedding = data['embedding']
        else:
            speaker = []
            speaker_embedding = []
        print("speaker and speaker_embedding",speaker,speaker_embedding)

        try:
            # speaker = []
            # speaker_embedding = []
            for voice_sample in voice_samples:
                try:
                    embedding = manager.get_embeddings_from_wav(voice_sample)
                except:
                    continue
                filename = os.path.basename(voice_sample)

                if not EmbeddingModel.find_by_attendee_id(attendee_id):
                    speaker.append(attendee_id)
                    speaker_embedding.append(embedding)
                    print("New Attendee")
            wfile = open(embedding_file,"wb")
            data = {"speaker":speaker,"embedding":speaker_embedding}
            wfile.write(pickle.dumps(data))
            wfile.close()
            
        except Exception :
            return {"Message":TRAINING_FAILED.format(attendee_id), "Error": str(e)},400
        
        # # keep record of audio id and attendee id
        # try:
        #     statement = attendee_audio.insert().values(audio_id=audio_id, attendee_id=attendee_id)
        #     try:
        #         db.session.execute(statement)
        #         db.session.commit()
        #     except Exception as e:
        #         # return {"Message":"Something error in server"},500
        #         # return {"Message":str(e)},500
        #         pass
        # except:
        #     pass
    

        # Keep record of voice samples of the attendee
        for voice_sample in voice_samples:
            emb = EmbeddingModel(None, None)
            emb.attendee_id = attendee_id
            emb.filename = os.path.basename(voice_sample)

            try:
                emb.save_to_db()
            except:
                pass

            del emb

        return {"success":True, "message":TRAINING_SUCCESSFUL.format(attendee_id)},200




# class DeleteAttendee(Resource):
#     @classmethod
#     def delete(cls, organization_id, attendee_id):
#         if OrganizationModel.find_by_id(organization_id) is None:
#             return {
#                        "data": {},
#                        "success": False,
#                        "message": ORGANIZATION_DOES_NOT_EXIST.format(organization_id)
#                    }, 400
#         if AttendeeModel.find_by_id(attendee_id) is None:
#             return {
#                        "data": {},
#                        "success": False,
#                        "message": ATTENDEE_DOES_NOT_EXIST.format(attendee_id)
#                    }, 400
            
#         embedding_file = os.path.join(PATH_EMBEDDING,"embedding.pickle")
        
#         audios = AudioModel.query.filter(AudioModel.attendee.any(id=attendee_id)).all()
#         for audio in audios:
#             filename = audio_helper.get_basename(audio.path)

#             basename = filename.split(".")[0]
#             json_filename = ".".join((basename, "json"))
           
#             # update recognized_speaker(replace respective attendee detail by "Unknown") in audio json file 
            
#             all_json_files_edited = get_all_jsonfile_from_folder(MEETING_FOLDER_EDIT)
#             if json_filename in all_json_files_edited:
#                 json_filepath = os.path.join(PATH_JSON_MEETING_EDIT,json_filename)
#                 transcript_data = json_helper.read_json(json_filepath)
#                 transcript_data = replace_attendee_detail_by_unknown(transcript_data,attendee_id)
#                 # for key,value in transcript_data["recognized_speakers"].items():
#                 #     if value == "Unknown":
#                 #         pass
#                 #     else:
#                 #         if value["id"] == attendee_id:
#                 #             transcript_data["recognized_speakers"][key] = "Unknown"
                            
#                 json_helper.write_json(json_filepath,transcript_data)
#                 # with open(json_filepath,'w') as write_file:
#                 #     json.dump(transcript_data,write_file)
            
            
#             json_filepath = os.path.join(PATH_JSON_MEETING, json_filename)
#             transcript_data = json_helper.read_json(json_filepath)
#             transcript_data = replace_attendee_detail_by_unknown(transcript_data,attendee_id)
                        
#             json_helper.write_json(json_filepath,transcript_data)      
            
#         # print(audios)

#         if os.path.exists(embedding_file):
#             data = pickle.loads(open(embedding_file,"rb").read())
#             print("print pickle data==========",data)
#             speakers = data["speaker"]
#             speaker_embeddings = data['embedding']
            
#             try:
#                 #create new list after removing elements of two list with same index
#                 speaker = [speaker for speaker_embedding, speaker in zip(speaker_embeddings, speakers) if speaker != attendee_id ]
#                 speaker_embedding = [speaker_embedding for speaker_embedding, speaker in zip(speaker_embeddings, speakers) if speaker != attendee_id  ]
                
#                 wfile = open(embedding_file,"wb")
#                 data = {"speaker":speaker,"embedding":speaker_embedding}
#                 wfile.write(pickle.dumps(data))
#                 wfile.close()
            
#                 # embedding_objs = EmbeddingModel.find_by_attendee_id(attendee_id)
#                 embedding_objs = EmbeddingModel.query.filter_by(attendee_id=attendee_id).delete()
#                 # embedding_objs.delete_from_db()
#                 db.session.commit()
                
#                 attendee_obj = AttendeeModel.find_by_id(attendee_id)
#                 attendee_obj.delete_from_db()
                
#                 # remove attendee voice samples folder of respective attendee 
#                 file_folder = os.path.join(PATH_ATTENDEE_VOICE_SAMPLE,str(attendee_id))
#                 print(file_folder)

#                 if os.path.exists(file_folder):
#                     shutil.rmtree(file_folder)

#             except Exception as e:
#                 return {"data":
#                             {
#                             },
#                         "message": "Something goes error in server",
#                         # "message": str(e),
#                         "success": False
#                     }, 500           
            
#             return {"data":
#                 {
#                 },
#                     "message": ATTENDEE_DELETEDED_SUCCESSFULLY,
#                     "success": True
#                    }, 200
#         else:
#             return {"data":
#                         {
#                         },
#                        "message": "Embedding file doesn't exist",
#                        "success": False
#                    }, 400
            
        
        
            


