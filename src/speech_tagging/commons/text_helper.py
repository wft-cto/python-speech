import json
import glob
import re
from typing import Union
from werkzeug.datastructures import FileStorage
from marshmallow import ValidationError

from flask_uploads import UploadSet, TEXT

from src.speech_tagging.definitions import *
from src.speech_tagging.commons.utils import get_all_json_filepaths

TEXT_FILE_SET = UploadSet("files", TEXT)  # set name and allowed extensions


def save_text_file(textfile: FileStorage, folder: str = None, name: str = None) -> str:
    return TEXT_FILE_SET.save(textfile, folder, name)


# for all json files
def concatenated_text_file(folder: str=None):
    path_jsonfiles = get_all_json_filepaths(folder)
    transcript_list = []
    for path_jsonfile in path_jsonfiles:
        with open(path_jsonfile,"r") as jsonfile:
            transcribe_data = json.load(jsonfile)
        # print(type(transcribe_data))
        # # transcript = transcribe_data["results"][0]["alternatives"][0]["transcript"]
        # alternatives = transcribe_data["results"]
        # # print(alternatives)
        for data in transcribe_data:
            # print(alternative)
            # transcript = alternative["alternatives"][0]["transcript"]
            transcript = data["vocal"]
            transcript_list.append(transcript)
    # for i in transcript_list:   
    #     print(i) 
        
    filepath = os.path.join(PATH_FILES_UPDATED_TRANSCRIBE,"updated_transcribe.txt")        
    with open(filepath,"w") as file:
        for each_line in transcript_list:   
            file.write(each_line)
            file.write("\n") 
   
        
def concatenate_vocal(json_filepath,text_filename):
    print("i am in concatenate vocal")
    transcript_list = []
    try:
        with open(json_filepath,"r") as jsonfile:
            transcribe_data = json.load(jsonfile)
        transcribe = transcribe_data["results"]
        # print(transcribe)
        for data in transcribe:
            # print(alternative)
            # transcript = alternative["alternatives"][0]["transcript"]
            transcript = data["vocal_without_tag"]
            transcript_list.append(transcript)
        # for i in transcript_list:   
        #     print(i) 
            
        filepath = os.path.join(PATH_FILES_UPDATED_TRANSCRIBE,text_filename)        
        with open(filepath,"w") as file:
            for each_line in transcript_list:   
                file.write(each_line)
                file.write("\n") 
    except Exception as e:
        print("********* Error in concatenate vocal ***********")
        # print(str(e))
        raise
        return {"message":str(e)},500