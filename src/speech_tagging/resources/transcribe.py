import json
import logging

from datetime import datetime
from flask import current_app as app
from flask import request
from flask_restful import Resource

from speech_tagging.watson_speech.watson_audio import WatsonSpeech
from speech_tagging.watson_speech import json_helper
from speech_tagging.watson_speech.custom_language_model import CustomLanguageModel

from speech_tagging.commons.extract_actions import ExtractAction
from speech_tagging.commons.entity_recognition import recognize_ents
from speech_tagging.commons.utils import get_all_filename_from_folder, get_all_jsonfile_from_folder
from speech_tagging.commons.messages import *
from speech_tagging.commons import audio_helper, text_helper, recognition_helper

from speech_tagging.definitions import *

from speech_tagging.models.organization import OrganizationModel
from speech_tagging.models.language_model import LanguageModelModel
from speech_tagging.models.attendee import attendee_audio
from speech_tagging.models.corpus import CorpusModel
from speech_tagging.models.attendee import AttendeeModel
from speech_tagging.models.audio import AudioModel

from speech_tagging.schemas.audio import AudioModelSchema
from speech_tagging.db import db

watson_language_model = CustomLanguageModel()

audio_model_schema = AudioModelSchema()

ws = WatsonSpeech()
ea = ExtractAction()

def add_marktag_transcript(transcript_text,action_phrase):
    vocal = transcript_text
    vocal_as_list = list(transcript_text)
    for action in action_phrase:
        start_position = action["start_position"]
        end_position = action["end_position"]
        for index,letter in enumerate(vocal):
            if index == start_position:
                start_letter = "<mark>" + vocal[index]
                vocal_as_list[index] = start_letter
            if index == end_position:
                end_letter = vocal[index] + "</mark>"
                vocal_as_list[index] = end_letter
    
    vocal_after_adding_mark_tag = "".join(vocal_as_list)
    return vocal_after_adding_mark_tag

def lookahead(iterable):
    """Pass through all values from the given iterable, augmented by the
    information if there are more values to come after the current one
    (True), or if it is the last value (False).
    """
    # Get an iterator and pull the first value.
    it = iter(iterable)
    last = next(it)
    # Run the iterator to exhaustion (starting from the second value).
    for val in it:
        # Report the *previous* value (more to come).
        yield last, True
        last = val
    # Report the last value.
    yield last, False
    
def format_transcript(transcript):
    speaker_labels = transcript["speaker_labels"]
    alternatives = transcript["results"]
    
    transcript_list = []
    transcript_text_list = []
    transcript_time_list = []
    # for accessing each object of speaker_labels
    index = 0
    initial_speaker = speaker_labels[0]["speaker"]
    for alternative in alternatives:
        alternative_data = alternative["alternatives"][0]
    
        timestamps = alternative_data["timestamps"]
        for timestamp,has_more in lookahead(timestamps):
            timestamp.append(speaker_labels[index]["speaker"])          
            if timestamp[3] == initial_speaker:
                if (speaker_labels[index]["from"] == timestamp[1] and speaker_labels[index]["to"] == timestamp[2]):
                    transcript_time_list.append(timestamp[1])
                    transcript_time_list.append(timestamp[2])
                    transcript_text_list.append(timestamp[0])
                    
                    # check whether is it last item of that loop
                    if (has_more == False):
                        # print("last timestamp",timestamp[0])
                        transcript_text = " ".join(transcript_text_list) 
                        transcript_text = transcript_text.replace("%HESITATION","")
                        transcript_text_original = transcript_text
                        if len(transcript_text) > 0:
                            # print(transcript_text)
                            # get action phrase from the transcripted text
                            action_phrase = ea.check_imperative(transcript_text)
                            # recognize_entities = None
                            if action_phrase is not None:
                                # here transcript_text is vocal with mark tag
                                transcript_text = add_marktag_transcript(transcript_text,action_phrase)
                                # recognize name(assign to) and date(due date) in action
                                # action_phrase = recognize_ents(action_phrase)
                                action_phrase = recognize_ents(transcript_text, action_phrase)
                            else:
                                action_phrase = []
              
                            if transcript_time_list:                   
                                transcript_dict = {
                                    "speaker": initial_speaker,
                                    "from": min(transcript_time_list),
                                    "to": max(transcript_time_list),
                                    "vocal": transcript_text,
                                    "vocal_without_tag": transcript_text_original,
                                    "action_phrase": action_phrase,
                                    # "recognize_entities": recognize_entities
                                }
                            # if len(transcript_text) != 0:
                            transcript_list.append(transcript_dict)
                            transcript_text_list = []
                            transcript_time_list = []

                    
            elif timestamp[3] != initial_speaker:
                # print("first speaker mismatch-----",timestamp[0])
                # print(transcript_text_list)
                # print(transcript_time_list)
                transcript_text = " ".join(transcript_text_list)
                transcript_text = transcript_text.replace("%HESITATION","")
                # # get action phrase from the transcripted text
                action_phrase = ea.check_imperative(transcript_text)
                if transcript_time_list:
                    transcript_dict = {
                        "speaker": initial_speaker,
                        "from": min(transcript_time_list),
                        "to": max(transcript_time_list),
                        # "vocal": transcript_text,
                        # "action_phrase": action_phrase
                    }
                if len(transcript_text) > 0:
                    transcript_text_original = transcript_text
                    # get action phrase from the transcripted text
                    action_phrase = ea.check_imperative(transcript_text)
                    # recognize_entities = None
                    if action_phrase is not None:
                        # here transcript_text is vocal with mark tag
                        transcript_text = add_marktag_transcript(transcript_text,action_phrase)
                        # recognize name(assign to) and date(due date) in action
                        # action_phrase = recognize_ents(action_phrase)
                        action_phrase = recognize_ents(transcript_text, action_phrase)
                    else:
                        action_phrase = []

                    
                    transcript_dict.update({"vocal": transcript_text,
                                            "vocal_without_tag": transcript_text_original,
                                            "action_phrase": action_phrase,
                                            # "recognize_entities": recognize_entities
                                            })             
                    transcript_list.append(transcript_dict)
                transcript_text_list = []
                transcript_time_list = []
                
                # add first word mismatch to new list
                transcript_text_list.append(timestamp[0])
                
                transcript_time_list.append(timestamp[1])
                transcript_time_list.append(timestamp[2])
                initial_speaker = timestamp[3]
                
                if (has_more == False):
                    # print("last timestamp",timestamp[0])
                    transcript_text = " ".join(transcript_text_list)
                    transcript_text = transcript_text.replace("%HESITATION","")
                    transcript_text_original = transcript_text
                    if len(transcript_text) > 0:
                        # get action phrase from the transcripted text
                        action_phrase = ea.check_imperative(transcript_text) 
                        # recognize_entities = None
                        if action_phrase is not None:
                            # here transcript_text is vocal with mark tag
                            transcript_text = add_marktag_transcript(transcript_text,action_phrase)
                            # recognize name(assign to) and date(due date) in action
                            # action_phrase = recognize_ents(action_phrase)
                            action_phrase = recognize_ents(transcript_text, action_phrase)
                        else:
                            action_phrase = []

                                          
                        if transcript_time_list:                   
                            transcript_dict = {
                                "speaker": initial_speaker,
                                "from": min(transcript_time_list),
                                "to": max(transcript_time_list),
                                "vocal": transcript_text,
                                "vocal_without_tag": transcript_text_original,
                                "action_phrase": action_phrase,
                                # "recognize_entities": recognize_entities
                            }
                        transcript_list.append(transcript_dict)
                        transcript_text_list = []
                        transcript_time_list = []

            # increase index of speaker_labels
            index += 1
            
    return transcript_list
    


def recognize_speaker(filename,transcript,transcription_description,audio_id):
    basename = filename.split(".")[0]
    json_filename = ".".join((basename, "json"))
    json_filepath = os.path.join(PATH_JSON_MEETING, json_filename)
    speaker_chunk = json_helper.pipeline(json_filepath)

    app.logger.info(datetime.now())
    app.logger.info('recognize_speaker detail :')
    app.logger.info(json_filepath)
    app.logger.info(speaker_chunk)
    app.logger.info("\n")

    audio_object, ext = audio_helper.create_audio_segment_object(filename)

    app.logger.info(datetime.now())
    app.logger.info('audio object detail :')
    app.logger.info(audio_object)
    app.logger.info(ext)
    app.logger.info("\n")

    for chunk in speaker_chunk:
        id_ = chunk['speaker']
        audio_helper.trim_and_save_audio_from_chunk(audio_object,id_, ext, chunk, filename,
                                                    PATH_SPEAKER_RECOGNITION)

    try:
        final_speakers = recognition_helper.final_speakers()
        # remove items with None key value
        try:
            final_speakers.pop("None")
        except Exception as e:
            app.logger.info(datetime.now())
            app.logger.info('final speaker exception detail :')
            app.logger.info(str(e))
            app.logger.info("\n")           
            pass
        
        # keep record of audio id and recognized speaker(attendee id) in  attendee_audio table
        for key,value in final_speakers.items():
            if value == "Unknown":
                pass
            else:
                # keep record of audio id and attendee id
                
                # attendee_audio_obj = attendee_audio.query.filter_by(audio_id=audio_id).filter_by(attendee_id=attendee_id).first()
                # if attendee_audio_obj:
                #     pass
                try:
                    statement = attendee_audio.insert().values(audio_id=audio_id, attendee_id=value["id"])
                    try:
                        db.session.execute(statement)
                        db.session.commit()
                    except Exception as e:
                        app.logger.info(datetime.now())
                        app.logger.info('inner db exception detail :')
                        app.logger.info(str(e))
                        app.logger.info("\n")      

                        # return {"Message":"Something error in server"},500
                        # return {"Message":"this is error------------>" + str(e)},500
                        pass
                except:
                    app.logger.info(datetime.now())
                    app.logger.info('outer db exception detail :')
                    app.logger.info(str(e))
                    app.logger.info("\n")      
                    # return {"Message":" error outer------------>" + str(e)},500
                    pass
    except Exception as e:
        app.logger.info(datetime.now())
        app.logger.info('first exception detail :')
        app.logger.info(str(e))
        app.logger.info("\n")  

        # raise
        return {
                   "data": {},
                #    "message": "Speaker recognition fail------------>" + str(e),
                   "message":"Unable to transcribe" + "  " + str(e),
                   "success": False
               }, 400
        
    # format the transcript initially provided by IBM WATSON api

    transcript.update({"recognized_speakers": final_speakers})
    transcript.update(transcription_description)

    app.logger.info(datetime.now())
    app.logger.info('update transcription : \n')
    app.logger.info("\n") 

    ws.save_json(transcript, filename, request.method)

    app.logger.info(datetime.now())
    app.logger.info('update transcription : \n')
    app.logger.info("\n") 

    return transcript


class Transcribe(Resource):

    def get(self,organization_id,model_name,audio_id):
        """
        Function to get transcription from Watson Speech and recognize speaker
        :return:
        """
        # print(audio_id)

        if OrganizationModel.find_by_id(organization_id) is None:
            return {"data":
                        {},
                    "message": "Organization not found",
                    # "message": str(e),
                    "success": False
                    }, 400

        if model_name != "Default":
            model = LanguageModelModel.find_by_organization_id_and_model_name(organization_id,model_name)
            if model is None:
                return {"data":
                            {},
                        "message": "Lanugage Model  not found",
                        # "message": str(e),
                        "success": False
                        }, 400
            else:
                customization_id = model.customization_id
        else:
            customization_id = model_name

        audio_obj = AudioModel.find_by_id(audio_id)

        if audio_obj is None:
            return {"data":
                        {},
                    "message": "Audio not found",
                    # "message": str(e),
                    "success": False
                    }, 400

        transcription_description = {"meeting_details":{"model_name":model_name,"audio_id":audio_id,
                                    "audio_name": audio_obj.filename, "date":str(audio_obj.date)}}
        app.logger.info(datetime.now())
        app.logger.info('transcription description :')
        app.logger.info(transcription_description)
        app.logger.info("\n")

        filename = audio_helper.get_basename(audio_obj.path)
        basename = filename.split(".")[0]
        json_filename = ".".join((basename, "json"))
        
        app.logger.info(datetime.now())
        app.logger.info("json file detail")
        app.logger.info(filename)
        app.logger.info(json_filename)
        app.logger.info("\n")

        # logic for transcript json file updated 
        # all_json_files_edited = get_all_jsonfile_from_folder(MEETING_FOLDER_EDIT)
        # if json_filename in all_json_files_edited:
        #     json_filepath = os.path.join(PATH_JSON_MEETING_EDIT,json_filename)
        #     with open(json_filepath,"r") as file:
        #         transcript = json.load(file)
        #         # transcript = recognize_speaker(filename,transcript)
        #         # transcript.update(transcription_description)
        #     return {"message":TRANSCRIPTION_SUCCESSFUL,
        #             "success":True,
        #             "is_edited":True,
        #             "data":transcript}, 200

        # logic for transcript json file not updated
        all_json_files = get_all_jsonfile_from_folder(MEETING_FOLDER)
        if json_filename in all_json_files:
            json_filepath = os.path.join(PATH_JSON_MEETING,json_filename)
            # with open(json_filepath,"r") as file:
            #     transcript = json.load(file)
            
            # update recognized_speaker in audio json file 
            transcript_data = json_helper.read_json(json_filepath)
            app.logger.info(datetime.now())
            app.logger.info("transcript data- recognized_speakers")
            app.logger.info(transcript_data["recognized_speakers"])
            app.logger.info(transcript_data)
            app.logger.info("\n")


            founded_speakers = recognition_helper.find_speakers(transcript_data, audio_obj, audio_id)

            # print("founded_speakers >>>>>>>>>>", founded_speakers)

            # print(transcript_data["recognized_speakers"])
            # for key,value in transcript_data["recognized_speakers"].items():
            #     if value == "Unknown":
            #         pass
            #     else:
            #         attendee_id = transcript_data["recognized_speakers"][key]["id"]
            #         try:
            #             attendee = AttendeeModel.find_by_id(attendee_id)
            #             transcript_data["recognized_speakers"][key] = attendee.json()
            #         except:
            #             pass
                        
            # print("my data==========>",transcript_data["recognized_speakers"])      
            with open(json_filepath,'w') as write_file:
                json.dump(founded_speakers,write_file)
            
            return {"message":TRANSCRIPTION_SUCCESSFUL,
                    "success":True,
                    "is_edited":False,
                    "data":founded_speakers}, 200

        try:
            filename = audio_helper.get_basename(audio_obj.path)
            transcript,status = ws.transcribe_meeting(request.method, filename,customization_id)
            # print("status: ********************")
            # print(status)

            app.logger.info(datetime.now())
            app.logger.info("filename:")
            app.logger.info(filename)
            app.logger.info("status: ********************")
            app.logger.info(status)
            app.logger.info("\n")

            if status:
                formatted_transcript = format_transcript(transcript)
                # print("return: format transcript")
                app.logger.info(datetime.now())
                app.logger.info("return: format transcript \n")

                transcript = {
                    # "transcript_before_formatting":transcript_before_formatting,
                    "results": formatted_transcript
                }
                ws.save_json(transcript, filename, request.method)
                # print("save the json file")
                app.logger.info(datetime.now())
                app.logger.info("save the json file \n")
                transcript = recognition_helper.find_speakers(transcript, audio_obj, audio_id)
                # transcript = recognize_speaker(filename,transcript,transcription_description,audio_id)
                # print("recognized speaker.............")
                app.logger.info(datetime.now())
                app.logger.info(" recognieze speaker........ \n")
                # transcript.update(transcription_description)

                return {"message":TRANSCRIPTION_SUCCESSFUL,
                        "success":True,
                        "is_edited":False,
                        "data":transcript}, 200
            else:
                # return {"message":transcript}, 400
                return {
                        "data":{},
                        "message":transcript,
                        "success":False
                        }, 400
        except Exception as err:
            # raise
            return {
                    "data":{},
                    # "message":AUDIO_TRANSCRIPTION_FAILED.format(""),
                    "message":str(err),
                    "success":False
                    }, 500

def is_custom_model_available():
    language_model_obj = LanguageModelModel.find_by_model_name("custom_model")
    if language_model_obj is None:
        return False
    else:
        return language_model_obj
    
def create_custom_model():
    language_model_obj = LanguageModelModel()
    language_model_obj.organization_id = 1
    language_model_obj.model_name = "custom_model"
    language_model_obj.model_description = "This is custom model"
    
    try:
        customization_id = watson_language_model.create_language_model(language_model_obj.model_name,language_model_obj.model_description)
        language_model_obj.customization_id = customization_id
        language_model_obj.save_to_db()
    except Exception as e:
        return {
            "data":{},
            "success":False,
            "message":"Unable to create language model"
            # "message":"Something goes error in server"
        }, 500
    print("===================in create custom model")
    return language_model_obj
    
# def create_corpus_text_file():
#     text_helper.concatenate_vocal(PATH_JSON_MEETING)
    
def add_corpus(text_filename,model):
    print("i am in add corpus module")
    print(text_filename)
    corpus_obj = CorpusModel.find_by_corpus_name(text_filename)
    if corpus_obj is None:
        filepath = os.path.join(PATH_FILES_UPDATED_TRANSCRIBE,text_filename)
        corpus_obj = CorpusModel()
        corpus_obj.organization_id = 1
        corpus_obj.corpus_name = text_filename
        corpus_obj.corpus_path = filepath
        try:
            corpus_obj.save_to_db()
            customization_id = model.customization_id
            success = watson_language_model.add_text_corpus(
                                                            customization_id=customization_id, 
                                                            corpus_name=text_filename, 
                                                            text_path=filepath)

        except Exception as e:
            return {
                "data":{},
                "success":False,
                "message":"Unable to add corpus"
                # "message":"Something goes error in server"
            }, 500  
        
        
def train_custom_model(model):
    print("i am in train custom module")
    try:
        watson_language_model.train_language_model(model.customization_id)
    except Exception as e:
        return {"data":
            {
            },
                    "message": "Training of {} failed. Please check if there is text corpus available for the model".format(model.model_name),
                    "success": False
                }, 500
    
    

class UpdateTranscribeJsonFile(Resource):
    def post(self,audio_id):
        """
        Function to post updated  transcripted json file
        :return:
        """
        # print(audio_id)
        audio_obj = AudioModel.find_by_id(audio_id)
        if audio_obj is None:
            return {"data":
                        {},
                    "message": "Audio not found",
                    # "message": str(e),
                    "success": False
                    }, 400            
        
        
        transcribe_json = request.get_json()
        # app.logger.info(transcribe_json)
        # transcript = transcribe_json['transcribe']
        transcript = transcribe_json
        # print(transcript)
        # if transcribe_json['transcribe']:
        #     pass
        # else:
        #     return {"message":"Invalid data: key error"}, 400
        # all_audio_files = get_all_filename_from_folder(USER_AUDIO_FOLDER)
        # if filename not in all_audio_files:
        #     return {"message": AUDIO_NOT_FOUND.format(filename)}, 400
        
        try:
            filename = audio_helper.get_basename(audio_obj.path)
            
            basename = filename.split(".")[0]
            json_filename = ".".join((basename, "json"))
            text_filename = ".".join((basename, "txt"))
            json_filepath = os.path.join(PATH_JSON_MEETING,json_filename)
            # all_json_files_edited = get_all_jsonfile_from_folder(MEETING_FOLDER_EDIT)
        
            # if json_filename in all_json_files_edited:
            #     edited = True
            # else:
            #     edited = False

            
            try:
                ws.save_json(transcript, filename, request.method)
            except Exception as err:
                return {#"message":"Unable to save updated jsonfile",
                        "message":str(err),
                        "success":False,
                        "data":{}}, 500
                
            language_model = is_custom_model_available()
            if language_model:
                print("language model available")
                pass
            else:
                print("model not available...now creating")
                language_model = create_custom_model()
                
            # create_corpus_text_file()
            text_helper.concatenate_vocal(json_filepath,text_filename)
            add_corpus(text_filename,language_model)
            train_custom_model(language_model)    
            
            
            
            return {"message":"Audio transcription jsonfile updated successfully",
                    "success":True,
                    "data":transcript}, 200
        except Exception as err:
            # raise
            return {"message":str(err)}, 500
            # return {"message":AUDIO_TRANSCRIPTION_FAILED.format(filename)}, 500

class GetTextFile(Resource):
    def get(self):
        print("hello concatenate")
        text_helper.concatenated_text_file(PATH_JSON_MEETING_EDIT)
        return {"message":"Combined transcription text file created successfully",
                "success":True,
                "data":{}}, 200       

# # class GetTranscribeJsonFile(Resource):
# #     def get(self,audio_id):
# #         try:
# #             audio_obj = AudioModel.query.get(audio_id)
# #             filename = audio_helper.get_basename(audio_obj.path)
# #         except Exception as e:
# #             return {"message":"Invalid audio_id"}
# #         # print(filename)
        
# #         basename = filename.split(".")[0]
# #         json_filename = ".".join((basename, "json"))
        
        
# #         all_json_files_edited = get_all_jsonfile_from_folder(MEETING_FOLDER_EDIT)
# #         # print(all_json_files_edited)
        

        
#         if json_filename in all_json_files_edited:
#             json_filepath_edit = os.path.join(PATH_JSON_MEETING_EDIT, json_filename)
#             with open(json_filepath_edit, 'r') as f:
#                 transcribe = json.load(f)
#                 # print(transcribe)

#             return {
#                     "data":{
#                         "audio":audio_model_schema.dump(audio_obj),
#                         "is_edit":True,
#                         "transcribe":transcribe
#                         },
#                     "success":True
#                     }
#         else:
#             json_filepath_original = os.path.join(PATH_JSON_MEETING, json_filename)
#             with open(json_filepath_original, 'r') as f:
#                 transcribe = json.load(f)
#             return {
#                     "data":{
#                         "audio":audio_model_schema.dump(audio_obj),
#                         "is_edit":False,
#                         "transcribe":transcribe
#                         },
#                     "success": True              
#                     }
            

