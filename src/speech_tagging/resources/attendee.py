import os
import json
import pickle
import shutil
from speech_tagging.db import db
import wave
import struct

from flask_restful import Resource
from flask import request
from speech_tagging.models.audio import AudioModel
from speech_tagging.models.attendee import AttendeeModel, attendee_audio
from speech_tagging.models.embedding import EmbeddingModel

from speech_tagging.schemas.attendee import AttendeeSchema, AttendeeVoiceSchema
from speech_tagging.models.organization import OrganizationModel
from speech_tagging.commons.messages import *
from speech_tagging.commons.audio_helper import *
from speech_tagging.commons.utils import get_all_filename_from_folder

from speech_tagging.commons import audio_helper
from speech_tagging.watson_speech import json_helper
from speech_tagging.commons.utils import get_all_jsonfile_from_folder
from speech_tagging.definitions import *

from speech_tagging.schemas.organization import OrganizationSchema
from speech_tagging.schemas.audio import AudioModelSchema

import pveagle
import dotenv

dotenv.load_dotenv(PATH_ENV)

organization_schema = OrganizationSchema()
audios_model_schema = AudioModelSchema(many=True)


attendee_schema = AttendeeSchema()
attendee_list_schema = AttendeeSchema(many=True)
voice_schema = AttendeeVoiceSchema()


def replace_attendee_detail_by_unknown(transcript_data,attendee_id):
    for key,value in transcript_data["recognized_speakers"].items():
        if value == "Unknown":
            pass
        else:
            if value["id"] == attendee_id:
                transcript_data["recognized_speakers"][key] = "Unknown"
    return transcript_data

class AttendeeRegister(Resource):

    @classmethod
    def post(cls):
        """

        :param audio_link:
        :return:
        """
        attendee_json = request.get_json()
        attendee = attendee_schema.load(attendee_json)

        organization_id = attendee_json.get("organization_id")
        email = attendee_json.get("email")
        phone = attendee_json.get("phone")

        if OrganizationModel.find_by_id(organization_id) is None:
            return {
                       "data": {},
                       "success": False,
                       "message": ORGANIZATION_DOES_NOT_EXIST.format(organization_id)
                   }, 400

        if AttendeeModel.find_by_organization_id_and_email(organization_id,email) is not None:
            return {
                       "data": {},
                       "success": False,
                       "message": ATTENDEE_ALREADY_EXISTS.format(email)
                   }, 400

        if AttendeeModel.find_by_organization_id_and_phone(organization_id, phone) is not None:
            return {
                       "data": {},
                       "success": False,
                       "message": "Attendee with phone number {}  already exists".format(phone)
                   }, 400

        try:
            attendee.save_to_db()
        except:
            return {"message": ERROR_INSERTING}, 500

        return {
                   "data": {"attendee":attendee_schema.dump(attendee)},
                   "success": True,
                   "message": ATTENDEE_ADDED_SUCCESSFULLY
               }, 200

class Attendee(Resource):

    @classmethod
    def get(cls,attendee_id):
        """

        :return:
        """
        attendee_obj = AttendeeModel.find_by_id(attendee_id)
        if attendee_obj is None:
            return {"data": 
                            {},
                    "message":"Attendee not Found",
                    "success":"False"
                    }, 404            
        attendee_detail = attendee_schema.dump(attendee_obj)
        
        organization_obj = OrganizationModel.find_by_id(attendee_obj.organization_id)
        if organization_obj is None:
            return {"data": 
                            {},
                    "message":"Organization not Found",
                    "success":"False"
                    }, 404                   
        
        organization_detail = organization_schema.dump(organization_obj)


        audios = AudioModel.query.filter(AudioModel.attendee.any(id=attendee_id)).all()
        # print(audios)
        # audios = AudioModel.query.filter_by(user_id=user_id).order_by(asc(AudioModel.filename))
        # print(audios)
        audios = audios_model_schema.dump(audios)
        all_detail = {
            "attendee":attendee_detail,
            "organization":organization_detail,
            "audios":audios
        }
        

        return {
                "data": all_detail,
                "message":"Attendee detail retrive successfully",
                "success":True
            }, 200


    @classmethod
    def put(cls,attendee_id):
        """

        :param audio_link:
        :return:
        """
        attendee_json = request.get_json()

        organization_id = attendee_json.get("organization_id")
        email = attendee_json.get("email")
        phone = attendee_json.get("phone")

        attendee_obj = AttendeeModel.find_by_id(attendee_id)
        if attendee_obj is None:
            return {
                       "data": {},
                       "success": False,
                       "message": ATTENDEE_DOES_NOT_EXIST.format(attendee_id)
                   }, 400

        if OrganizationModel.find_by_id(organization_id) is None:
            return {
                       "data": {},
                       "success": False,
                       "message": ORGANIZATION_DOES_NOT_EXIST.format(organization_id)
                   }, 400

        try:
            attendee_obj.first_name = attendee_json.get("first_name")
            attendee_obj.last_name = attendee_json.get("last_name")
            attendee_obj.gender = attendee_json.get("gender")
            attendee_obj.email = email
            attendee_obj.phone = phone
            attendee_obj.organization_id = organization_id

            attendee_obj.save_to_db()
        except Exception as e:
            # return {"message": ERROR_INSERTING}, 500
            return {"message": str(e)}, 500

        return {
                   "data": {"attendee":attendee_schema.dump(attendee_obj)},
                   "success": True,
                   "message": ATTENDEE_UPDATED_SUCCESSFULLY
               }, 200


class AllAttendee(Resource):
    @classmethod
    def get(cls):
        """

        :return:
        """
        attendees = AttendeeModel.find_all()
        result = {}
        for attendee in attendees:
            intro = attendee.first_name + " " + attendee.last_name + " (" + attendee.email + ")"
            result.update({attendee.id: intro})
        return {"data": result}, 200


class AttendeeVoice(Resource):

    @classmethod
    def post(cls):
        """

        :return:
        """
        attendee_voice_json = request.get_json()
        attendee_voice = voice_schema.load(attendee_voice_json)

        attendee_id = attendee_voice["attendee_id"]
        # audio_name = attendee_voice["audio_name"]
        audio_id = attendee_voice["audio_id"]
        voice_list = attendee_voice["voice_list"]
        attendee_obj = AttendeeModel.find_by_id(attendee_id)

        FEEDBACK_TO_DESCRIPTIVE_MSG = {
            pveagle.EagleProfilerEnrollFeedback.AUDIO_OK: 'Good audio',
            pveagle.EagleProfilerEnrollFeedback.AUDIO_TOO_SHORT: 'Insufficient audio length',
            pveagle.EagleProfilerEnrollFeedback.UNKNOWN_SPEAKER: 'Different speaker in audio',
            pveagle.EagleProfilerEnrollFeedback.NO_VOICE_FOUND: 'No voice found in audio',
            pveagle.EagleProfilerEnrollFeedback.QUALITY_ISSUE: 'Low audio quality due to bad microphone or environment'
        }

        if not AttendeeModel.find_by_id(attendee_id):
            print("HERE")
            return {"message":ATTENDEE_DOES_NOT_EXIST.format(attendee_id)}

        all_audio_files = get_all_filename_from_folder(MEETING_FOLDER)

        audio_obj = AudioModel.query.get(audio_id)
        audio_filename = audio_helper.get_basename(audio_obj.path)

        if audio_filename not in all_audio_files:
            print("HERE1")
            return {"message": AUDIO_ALREADY_EXISTS.format(audio_name)}, 400

        try:
            # print("HERE")
            audio_object,extension = create_audio_segment_object(audio_filename)

            filename = attendee_obj.first_name + '-' + str(attendee_id) + '.txt'
            # print(filename)
            all_speaker_files = get_all_filename_from_folder(SPEAKER_FOLDER)
            # print(all_speaker_files)
            if filename in all_speaker_files:
                return {"message":VOICE_SAMPLE_ALREADY_EXISTS}, 400

            for voice_time in voice_list:
                voice_chunk = {
                    "from": voice_time['start'],
                    "to": voice_time['end']
                }

                print(audio_object)

                trimmed_audio = trim_and_save_audio_from_chunk(audio_object,attendee_id,'wav',voice_chunk,audio_filename.split('.')[0], PATH_ATTENDEE_VOICE_SAMPLE)
                print(trimmed_audio)


                try:
                    # print("Model Path +++++++++", args.access_key, args.model_path, args.library_path)
                    eagle_profiler = pveagle.create_profiler(
                        access_key=os.environ.get("PICOVOICE_KEY"))
                    # print("profiler created")
                except pveagle.EagleError as e:
                    print("Failed to initialize EagleProfiler: ", e)
                    raise

                print('Eagle version: %s' % eagle_profiler.version)

                try:
                    print("Eagle Sample Rate on storing it :", eagle_profiler.sample_rate)
                    enroll_percentage = 0.0

                    with wave.open(trimmed_audio, mode="rb") as wav_file:
                        # print('open')
                        channels = wav_file.getnchannels()
                        sample_width = wav_file.getsampwidth()
                        num_frames = wav_file.getnframes()
                        # print("channels>>>>>",channels, "smaple_width>>>>", sample_width, "num_frames>>>>",num_frames)

                        if wav_file.getframerate() != eagle_profiler.sample_rate:
                            raise ValueError(
                            "Audio file should have a sample rate of %d. got %d" % (sample_rate, wav_file.getframerate()))
                        if sample_width != 2:
                            raise ValueError("Audio file should be 16-bit. got %d" % sample_width)
                        if channels == 2:
                            print("Eagle processes single-channel audio but stereo file is provided. Processing left channel only.")

                        samples = wav_file.readframes(num_frames)

                    # print(samples)

                    frames = struct.unpack('h' * num_frames * channels, samples)

                    audio =  frames[::channels]
                    # print(audio)
                    enroll_percentage, feedback = eagle_profiler.enroll(audio)
                    # print("HERE1")
                    print('Enrolled audio file %s [Enrollment percentage: %.2f%% - Enrollment feedback: %s]'
                        % (attendee_id, enroll_percentage, FEEDBACK_TO_DESCRIPTIVE_MSG[feedback]))

                    while enroll_percentage < 100.0: 
                        enroll_percentage, feedback = eagle_profiler.enroll(audio)
                        print('Enrolled audio file %s [Enrollment percentage: %.2f%% - Enrollment feedback: %s]'
                            % (attendee_id, enroll_percentage, FEEDBACK_TO_DESCRIPTIVE_MSG[feedback]))

                    if enroll_percentage < 100.0:
                        print('Failed to create speaker profile. Insufficient enrollment percentage: %.2f%%. '
                            'Please add more audio files for enrollment.' % enroll_percentage)
                    else:
                        speaker_profile = eagle_profiler.export()
                        # attendee_obj.voice_id = speaker_profile
                        with open(PATH_SPEAKER_RECOGNITION+str('/'+ attendee_obj.first_name + '-' +  str(attendee_id))+'.txt' , 'wb') as f:
                            f.write(speaker_profile.to_bytes())
                        print('Speaker profile is saved to', speaker_profile)
                except Exception  as e:
                    print('Error: ', e)
                except pveagle.EagleActivationLimitError:
                    print('AccessKey has reached its processing limit')
                except pveagle.EagleError as e:
                    print('Failed to perform enrollment: ', e)
                finally:
                    eagle_profiler.delete()



            # del audio_object
        except Exception as e:
            print("Error :", e)
            return {"message":VOICE_SAMPLE_SAVE_FAIL}, 500

        return {"message":VOICE_SAMPLE_REGISTERED}, 200


# class AttendeeDetail(Resource):
#     @classmethod
#     def get(cls,attendee_id):
#         """

#         :return:
#         """
#         attendee_obj = AttendeeModel.find_by_id(attendee_id)
#         if attendee_obj is None:
#             return {"data": 
#                             {},
#                     "message":"Attendee not Found",
#                     "success":"False"
#                     }, 404            
#         attendee_detail = attendee_schema.dump(attendee_obj)
        
#         organization_obj = OrganizationModel.find_by_id(attendee_obj.organization_id)
#         if organization_obj is None:
#             return {"data": 
#                             {},
#                     "message":"Organization not Found",
#                     "success":"False"
#                     }, 404                   
        
#         organization_detail = organization_schema.dump(organization_obj)


#         audios = AudioModel.query.filter(AudioModel.attendee.any(id=attendee_id)).all()
#         # print(audios)
#         # audios = AudioModel.query.filter_by(user_id=user_id).order_by(asc(AudioModel.filename))
#         # print(audios)
#         audios = audios_model_schema.dump(audios)
#         all_detail = {
#             "attendee":attendee_detail,
#             "organization":organization_detail,
#             "audios":audios
#         }
        

#         return {
#                 "data": all_detail,
#                 "message":"Attendee detail retrive successfully",
#                 "success":True
#             }, 200


class AttendeeDelete(Resource):
    @classmethod
    def delete(cls, organization_id, attendee_id):
        if OrganizationModel.find_by_id(organization_id) is None:
            return {
                       "data": {},
                       "success": False,
                       "message": ORGANIZATION_DOES_NOT_EXIST.format(organization_id)
                   }, 400
        if AttendeeModel.find_by_id(attendee_id) is None:
            return {
                       "data": {},
                       "success": False,
                       "message": ATTENDEE_DOES_NOT_EXIST.format(attendee_id)
                   }, 400
            
        
        audios = AudioModel.query.filter(AudioModel.attendee.any(id=attendee_id)).all()
        for audio in audios:
            filename = audio_helper.get_basename(audio.path)

            basename = filename.split(".")[0]
            json_filename = ".".join((basename, "json"))
           
            # update recognized_speaker(replace respective attendee detail by "Unknown") in audio json file 
            
            all_json_files_edited = get_all_jsonfile_from_folder(MEETING_FOLDER_EDIT)
            if json_filename in all_json_files_edited:
                json_filepath = os.path.join(PATH_JSON_MEETING_EDIT,json_filename)
                transcript_data = json_helper.read_json(json_filepath)
                transcript_data = replace_attendee_detail_by_unknown(transcript_data,attendee_id)
                # for key,value in transcript_data["recognized_speakers"].items():
                #     if value == "Unknown":
                #         pass
                #     else:
                #         if value["id"] == attendee_id:
                #             transcript_data["recognized_speakers"][key] = "Unknown"
                            
                json_helper.write_json(json_filepath,transcript_data)
                # with open(json_filepath,'w') as write_file:
                #     json.dump(transcript_data,write_file)
            
            
            json_filepath = os.path.join(PATH_JSON_MEETING, json_filename)
            transcript_data = json_helper.read_json(json_filepath)
            transcript_data = replace_attendee_detail_by_unknown(transcript_data,attendee_id)
                        
            json_helper.write_json(json_filepath,transcript_data)      
            
        # print(audios)

        embedding_file = os.path.join(PATH_EMBEDDING,"embedding.pickle")
        if os.path.exists(embedding_file):
            data = pickle.loads(open(embedding_file,"rb").read())
            # print("print pickle data==========",data)
            speakers = data["speaker"]
            speaker_embeddings = data['embedding']
            
            try:
                #create new list after removing elements of two list with same index
                speaker = [speaker for speaker_embedding, speaker in zip(speaker_embeddings, speakers) if speaker != attendee_id ]
                speaker_embedding = [speaker_embedding for speaker_embedding, speaker in zip(speaker_embeddings, speakers) if speaker != attendee_id  ]
                
                wfile = open(embedding_file,"wb")
                data = {"speaker":speaker,"embedding":speaker_embedding}
                wfile.write(pickle.dumps(data))
                wfile.close()
            
                # embedding_objs = EmbeddingModel.find_by_attendee_id(attendee_id)
                embedding_objs = EmbeddingModel.query.filter_by(attendee_id=attendee_id).delete()
                # embedding_objs.delete_from_db()
                db.session.commit()
                
                attendee_obj = AttendeeModel.find_by_id(attendee_id)
                attendee_obj.delete_from_db()
                
                # remove attendee voice samples folder of respective attendee 
                file_folder = os.path.join(PATH_ATTENDEE_VOICE_SAMPLE,str(attendee_id))
                # print(file_folder)

                if os.path.exists(file_folder):
                    shutil.rmtree(file_folder)

            except Exception as e:
                return {"data":
                            {
                            },
                        "message": "Something goes error in server",
                        # "message": str(e),
                        "success": False
                    }, 500           
            
            return {"data":
                {
                },
                    "message": ATTENDEE_DELETEDED_SUCCESSFULLY,
                    "success": True
                   }, 200
        else:
            return {"data":
                        {
                        },
                       "message": "Embedding file doesn't exist",
                       "success": False
                   }, 400
   