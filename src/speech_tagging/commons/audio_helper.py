import os
import re
import glob
import tempfile
from datetime import datetime

from pydub import AudioSegment
from typing import Union
from marshmallow import ValidationError
from werkzeug.datastructures import FileStorage

from flask import current_app as app
from flask_uploads import UploadSet, AUDIO, TEXT

import wave

from speech_tagging.definitions import *

AUDIO = AUDIO + ("webm", "mp4", "m4a")

AUDIO_SET = UploadSet("audios", AUDIO)  # set name and allowed extensions

def save_audio(audio: FileStorage, name: str = None, folder: str = None, ) -> str:
    return AUDIO_SET.save(audio, folder, name)


def convert_and_save_audio(audio: FileStorage, name: str = None, folder: str = None, ) -> str:
    app.logger.info("---------------- convert and save ----------------")
    extension = get_extension(name)
    org_file_path = os.path.join(PATH_AUDIO, MEETING_FOLDER, name)
    save_file_path = os.path.join(PATH_AUDIO, MEETING_FOLDER, name.replace(extension, ".mp3"))

    app.logger.info(org_file_path)
    app.logger.info(extension)

    # save file, if extension is mp3 do not convert
    temp_audio_path = save_audio(audio, name, folder)
    if extension == ".mp3":
        return temp_audio_path

    audio_object, ext = create_audio_segment_object(org_file_path)

    audio_object.export(save_file_path, format="mp3")
    app.logger.info("Saved as: ", audio_object, ext)

    # Remove original and save only .mp3
    try:
        os.remove(org_file_path)
    except Exception as e:
        app.logger.info(f"Could not delete file {org_file_path}")
        app.logger.info(str(e))

    app.logger.info(f"Original ---- {org_file_path}")
    app.logger.info(f"MP3 ---- {save_file_path}")

    return f"{folder}/{name.replace(extension, '.mp3')}"


def get_path(filename: str = None, folder: str = None) -> str:
    return AUDIO_SET.path(filename, folder)


def find_audio_any_format(filename: str, folder: str) -> Union[str, None]:
    """
    Given a format-less filename, try to find the file by appending each of the allowed formats to the given
    filename and check if the file exists
    :param filename: formatless filename
    :param folder: the relative folder in which to search
    :return: the path of the audio if exists, otherwise None
    """
    for _format in AUDIO:  # look for existing avatar and delete it
        avatar = filename.format(_format)
        avatar_path = AUDIO_SET.path(filename=avatar, folder=folder)
        if os.path.isfile(avatar_path):
            return avatar_path
    return None


def _retrieve_filename(file: Union[str, FileStorage]) -> str:
    """
    Make our filename related functions generic, able to deal with FileStorage object as well as filename str.
    """
    if isinstance(file, FileStorage):
        return file.filename
    return file


def is_filename_safe(file: Union[str, FileStorage]) -> bool:
    """
    Check if a filename is secure according to our definition
    - starts with a-z A-Z 0-9 at least one time
    - only contains a-z A-Z 0-9 and _().-
    - followed by a dot (.) and a allowed_format at the end
    """
    filename = _retrieve_filename(file)

    allowed_format = "|".join(AUDIO)
    # format AUDIOS into regex, eg: ('jpeg','png') --> 'jpeg|png'
    regex = "^[a-zA-Z0-9][a-zA-Z0-9_()-\.]*\.({})$".format(allowed_format)
    return re.match(regex, filename) is not None


def get_basename(file: Union[str, FileStorage]) -> str:
    """
    Return file's basename, for example
    get_basename('some/folder/audio.wav') returns 'audio.wav'
    """
    filename = _retrieve_filename(file)

    app.logger.info(datetime.now())
    app.logger.info("get_filename: ")
    app.logger.info(filename)
    app.logger.info("\n")

    return os.path.split(filename)[1]


def get_extension(file: Union[str, FileStorage]) -> str:
    """
    Return file's extension, for example
    get_extension('audio.wav') returns '.wav'
    """
    filename = _retrieve_filename(file)
    return os.path.splitext(filename)[1]


# def try_create_audio_segment_object(filename):
#     """
#     Create Pydub AudioSegment object according to audio file extension
#     :param filename:
#     :return:
#     """
#
#     file_path = os.path.join(PATH_AUDIO,MEETING_FOLDER,filename)
#     extension = get_extension(filename).split(".")[1]
#
#     try:
#         return AudioSegment.from_wav(file_path), extension
#     except:
#         pass
#     try:
#         return AudioSegment.from_mp3(file_path), extension
#     except:
#         pass
#     try:
#         return AudioSegment.from_ogg(file_path), extension
#     except:
#         pass
#     try:
#         return AudioSegment.from_flv(file_path), extension
#     except:
#         pass
#     # try:
#     return AudioSegment.from_file(file_path), extension
#     # except:
#         # raise ValidationError
#     #
#     #     return AudioSegment.from_wav(file_path), extension
#     # elif extension == "mp3":
#     #     return AudioSegment.from_mp3(file_path), extension
#     # elif extension == "ogg":
#     #     return AudioSegment.from_ogg(file_path), extension
#     # elif extension == "flv":
#     #     return AudioSegment.from_flv(file_path), extension
#     # elif extension == "wma" or "aac":
#     #     return AudioSegment.from_file(file_path,extension), extension
#     # else:
#     #     raise ValidationError
#     #
#     # return audio_segment


def create_audio_segment_object(filename):
    """
    Create Pydub AudioSegment object according to audio file extension
    :param filename:
    :return:
    """

    extension = get_extension(filename).split(".")[1]
    file_path = os.path.join(PATH_AUDIO,MEETING_FOLDER,filename)
    app.logger.info(extension)
    app.logger.info(file_path)

    if extension == "wav":
        return AudioSegment.from_wav(file_path), extension
    elif extension == "mp3":
        return AudioSegment.from_mp3(file_path), extension
    elif extension == "ogg":
        return AudioSegment.from_ogg(file_path), extension
    elif extension == "flv":
        return AudioSegment.from_flv(file_path), extension
    elif extension == "wma" or "aac" or "mp4" or "m4a":
        return AudioSegment.from_file(file_path,extension), extension
    else:
        raise ValidationError


def trim_and_save_audio(audio_object, extension, attendee_id, audio_time: dict, audio_name, path=PATH_ATTENDEE_VOICE_SAMPLE):
    """

    :param audio_object:
    :param extension:
    :param attendee_id:
    :param audio_time:
    :param audio_name:
    :param path:
    :return:
    """
    file_folder = os.path.join(path,str(attendee_id))
    if not os.path.exists(file_folder):
        os.makedirs(file_folder)

    start = audio_time["from"]
    end = audio_time["to"]
    file_name = "__".join((str(start),str(end), audio_name))
    file_path = os.path.join(file_folder,file_name)

    trimmed_audio = audio_object[start * 1000:end * 1000]
    trimmed_audio.export(file_path, format=extension)


def trim_and_save_audio_from_chunk(audio_object,id_,extension, chunk: dict, audio_name, path=PATH_ATTENDEE_VOICE_SAMPLE):
    """

    :param audio_object:
    :param extension:
    :param attendee_id:
    :param audio_time:
    :param audio_name:
    :param path:
    :return:
    """

    print("Audio Helper")
    start = chunk["from"]
    end = chunk["to"]
    
    file_folder = os.path.join(path,str(id_))

    if not os.path.exists(file_folder):
        os.makedirs(file_folder)
    if end - start > 1:
        try: 
            file_name = "__".join((str(start),str(end), audio_name))
            file_path = os.path.join(file_folder,file_name + '.wav')

            trimmed_audio = audio_object[start * 1000:end * 1000]
            trimmed_audio = trimmed_audio.set_frame_rate(16000)
            # print(file_name)
            # print(file_path)
            trimmed_audio.export(file_path, format=extension)

            return file_path
        
        except Exception as e:
            print("Audio Helper Error :", e)


