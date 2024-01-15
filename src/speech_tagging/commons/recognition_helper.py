import glob
import pickle
import random
from datetime import datetime

import numpy as np
from scipy.spatial.distance import cdist

from flask import current_app as app
from speech_tagging.definitions import *
from speech_tagging.speaker_recognition.manager import manager
from speech_tagging.models.attendee import AttendeeModel
from speech_tagging.commons import audio_helper
from speech_tagging.commons.utils import get_all_filename_from_folder, get_all_jsonfile_from_folder
import shutil

import os
import pveagle
import wave
import struct
from speech_tagging.models.audio import AudioModel

COST_METRIC = "cosine"  # euclidean or cosine
speaker = []
speaker_embedding = []


def load_data():
    global speaker
    global speaker_embedding
    try:
        file = os.path.join(PATH_EMBEDDING, "embedding.pickle")
        data = pickle.loads(open(file, "rb").read())
        speaker = data["speaker"]
        speaker_embedding = data['embedding']
    except Exception as Err:
        print("Error ::::", Err)
    return speaker, speaker_embedding


def delete_embedding_for_user(user_id):
    """

    :param user_id:
    :return:
    """
    file = os.path.join(PATH_EMBEDDING, "embedding.pickle")
    data = pickle.loads(open(file, "rb").read())
    speaker = data["speaker"]
    speaker_embedding = data['embedding']



def find_distance(speech_encodings, speech_to_compare):
    """
    """
    print(cdist(speech_encodings, speech_to_compare, metric=COST_METRIC))
    return cdist(speech_encodings, speech_to_compare, metric=COST_METRIC) if len(speech_encodings) > 0 else None
    # return np.linalg.norm(speech_encodings - speech_to_compare, axis=1) if len(speech_encodings) > 0 else None


def best_speaker_match(speech_encodings, speech_to_compare, tolerance):
    """
    :return:
    """
    distances = find_distance(speech_encodings, [speech_to_compare])
    if distances is not None:
        min_dist = min(distances)
        if min_dist < tolerance:
            return np.where(distances == min_dist)[0][0], min_dist

        return None, min_dist
    else:
        return None, None


def recognize():
    """
    Find speaker id by comparing it with
    :return:
    """

    def recognize_speaker():
        ""
        file = random.choice(files)
        try:
            embedding = manager.get_embeddings_from_wav(file)
            speaker_loc, dist = best_speaker_match(all_embedding, embedding, tolerance=0.27)
            if speaker_loc is None:
                speaker_id = "Unknown"
            else:
                speaker_id = all_speaker[speaker_loc]
            speakers.append(speaker_id)
        except Exception as err:
            print(file)
            print(err)

    # Load data
    all_speaker, all_embedding = load_data()
    result = {}
    sub_dirs = glob.glob(os.path.join(PATH_SPEAKERS, "*"))
    for sub_dir in sub_dirs:
        speaker = os.path.basename(sub_dir)
        files = glob.glob(os.path.join(sub_dir, "*"))
        speakers = []
        if len(files) > 15:
            for _ in range(15):
                recognize_speaker()
        else:
            for _ in range(len(files)):
                recognize_speaker()
        if len(speakers) == 0:
            speakers = ["Unknown"]
        final_speaker_id = max(set(speakers), key=speakers.count)
        result.update({speaker: final_speaker_id})
    return result


def final_speakers():
    """

    :return:
    """
    speakers = recognize()

    final_speakers = {}
    for key, value in speakers.items():
        if value != "Unknown":
            attendee = AttendeeModel.find_by_id(value)
            final_speakers.update({key: attendee.json()})
        else:
            final_speakers.update({key: value})

    app.logger.info(datetime.now())
    app.logger.info('final speaker detail :')
    app.logger.info(final_speakers)
    app.logger.info("\n")

    shutil.rmtree(PATH_SPEAKERS)
    return final_speakers


def read_file(file_name, sample_rate):
    with wave.open(file_name, mode="rb") as wav_file:
        channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        num_frames = wav_file.getnframes()

        if wav_file.getframerate() != sample_rate:
            raise ValueError(
                "Audio file should have a sample rate of %d. got %d" % (sample_rate, wav_file.getframerate()))
        if sample_width != 2:
            raise ValueError("Audio file should be 16-bit. got %d" % sample_width)
        if channels == 2:
            print("Eagle processes single-channel audio but stereo file is provided. Processing left channel only.")

        samples = wav_file.readframes(num_frames)

    frames = struct.unpack('h' * num_frames * channels, samples)

    return frames[::channels]


def find_speakers(transcript, audio_object, audio_id):
    # print(transcript)

    founded_speakers = {}

    try: 
        # audio_obj = AudioModel.query.get(audio_id)
        audio_filename = audio_helper.get_basename(audio_object.path)

        transcribe_json = transcript["results"]
        # print("transcribe_json", transcribe_json)

        audio_obj,extension = audio_helper.create_audio_segment_object(audio_filename)
        
        recognization_results = {}



        for segment in transcribe_json:
            # segment['speaker_recognized'] = False
            # if isinstance(segment['speaker'], int):
            start = segment['from']
            end = segment['to']
            if (end - start > 1):
                # Speaker Profiles 
                all_speakers = get_all_filename_from_folder(PATH_SPEAKER_RECOGNITION)

                speaker_profiles = []

                for speaker in all_speakers:
                    # speaker_labels.append(os.path.splitext(os.path.basename(file_paths))[0])
                    speaker_filepath = os.path.join(PATH_SPEAKER_RECOGNITION, speaker)
                    with open(speaker_filepath, 'rb') as f:
                        speaker_profiles.append(pveagle.EagleProfile.from_bytes(f.read()))

                # Print the list of file paths
                # print("File Paths:", speaker_profiles).

                # print(speaker_profiles)

                eagle = pveagle.create_recognizer(
                    access_key="/vF6q06PnydpPi9ITOeF9+PJHKnmOYUGjXCS58glpYgwGJ4CEHRICQ==",
                    speaker_profiles=speaker_profiles)

                voice_chunk = {
                    "from": segment['from'],
                    "to": segment['to']
                }

                trimmed_audio = audio_helper.trim_and_save_audio_from_chunk(audio_obj,audio_id,'wav',voice_chunk,audio_filename.split('.')[0], PATH_AUDIO_CLIPS)

                try:
                    audio = read_file(trimmed_audio, eagle.sample_rate)
                    # print("Eagle Sample Rate on Matching :", eagle.sample_rate)
                    # print(audio)
                    num_frames = len(audio) // eagle.frame_length
                    frame_to_second = eagle.frame_length / eagle.sample_rate
                    total_scores = 0
                    # print()
                    speaker_index = 0
                    for i in range(num_frames):
                        frame = audio[i * eagle.frame_length:(i + 1) * eagle.frame_length]
                        scores = eagle.process(frame)
                        # time = i * frame_to_second
                        # print("Score>>>>>>>>", scores)
                        largest_element = max(scores, key=lambda x: x)

                        if largest_element > 0:
                            total_scores = total_scores + 1
                            speaker_index = scores.index(largest_element)
                        # if 1.0 in scores:
                        #     total_scores = total_scores + 1     
                    print(speaker_index)
                    print(all_speakers)
                    print("total_scores >>>>",num_frames, "  resulted Scores >>>>>>>", total_scores)               

                    if ((total_scores * 100) / num_frames > 50):
                        speaker_id = (all_speakers[speaker_index]).split('.')[0].split('-')[1]
                        print(all_speakers[speaker_index])
                        # segment['speaker_recognized'] = True
                        speaker_id1 = int(speaker_id)
                        attendee = AttendeeModel.find_by_id(int(speaker_id1))
                        # segment["speaker_detail"] = attendee.json()
                        curId = segment['speaker'] 
                        strCurId = str(curId)
                        print(strCurId)
                        recognization_results[strCurId] = attendee.json()
                        for key,value in transcript["recognized_speakers"].items():
                            if key == strCurId:
                                transcript["recognized_speakers"][key] = attendee.json()
                                
                    
                    # transcript.update()
                    # print(recognization_results)

                except pveagle.EagleActivationLimitError:
                    print('AccessKey has reached its processing limit.')
                except pveagle.EagleError as e:
                    print("Failed to process audio: ", e)
                    raise
                finally:
                    eagle.delete()

        # print(recognization_results)
        # transcript['recognized_speakers'] = recognization_results
    
    except Exception as e:
        print("Error :", e)

    finally:
        # print(transcript)
        clips_folder_path = os.path.join(PATH_AUDIO_CLIPS, str(audio_id))
        all_speaker_audio_clips = get_all_filename_from_folder(PATH_AUDIO_CLIPS)
        if str(audio_id) in all_speaker_audio_clips:
            all_audio_clips_files = get_all_filename_from_folder(clips_folder_path)
            for audio_clip in all_audio_clips_files: 
                audio_clip_path = os.path.join(clips_folder_path, audio_clip)
                os.remove(audio_clip_path)
            os.rmdir(clips_folder_path)

        return transcript



if __name__ == "__main__":
    recognize()
