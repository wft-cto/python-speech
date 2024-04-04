import glob
import pickle
import random
from datetime import datetime

import numpy as np
import numpy
from scipy.spatial.distance import cdist

from flask import current_app as app
from speech_tagging.definitions import *
# from speech_tagging.speaker_recognition.manager import manager
from speech_tagging.models.attendee import AttendeeModel
from speech_tagging.commons import audio_helper
from speech_tagging.commons.utils import get_all_filename_from_folder, get_all_jsonfile_from_folder
import shutil

import os
import pveagle
import wave
import struct
from speech_tagging.models.audio import AudioModel
from collections import Counter

import scipy.cluster
import scipy.io.wavfile
from python_speech_features import mfcc
from sklearn import preprocessing
from sklearn.mixture import GaussianMixture


import librosa
from scipy.spatial.distance import euclidean

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


# def recognize():
#     """
#     Find speaker id by comparing it with
#     :return:
#     """

#     def recognize_speaker():
#         ""
#         file = random.choice(files)
#         try:
#             embedding = manager.get_embeddings_from_wav(file)
#             speaker_loc, dist = best_speaker_match(all_embedding, embedding, tolerance=0.27)
#             if speaker_loc is None:
#                 speaker_id = "Unknown"
#             else:
#                 speaker_id = all_speaker[speaker_loc]
#             speakers.append(speaker_id)
#         except Exception as err:
#             print(file)
#             print(err)

#     # Load data
#     all_speaker, all_embedding = load_data()
#     result = {}
#     sub_dirs = glob.glob(os.path.join(PATH_SPEAKERS, "*"))
#     for sub_dir in sub_dirs:
#         speaker = os.path.basename(sub_dir)
#         files = glob.glob(os.path.join(sub_dir, "*"))
#         speakers = []
#         if len(files) > 15:
#             for _ in range(15):
#                 recognize_speaker()
#         else:
#             for _ in range(len(files)):
#                 recognize_speaker()
#         if len(speakers) == 0:
#             speakers = ["Unknown"]
#         final_speaker_id = max(set(speakers), key=speakers.count)
#         result.update({speaker: final_speaker_id})
#     return result


# def final_speakers():
#     """

#     :return:
#     """
#     speakers = recognize()

#     final_speakers = {}
#     for key, value in speakers.items():
#         if value != "Unknown":
#             attendee = AttendeeModel.find_by_id(value)
#             final_speakers.update({key: attendee.json()})
#         else:
#             final_speakers.update({key: value})

#     app.logger.info(datetime.now())
#     app.logger.info('final speaker detail :')
#     app.logger.info(final_speakers)
#     app.logger.info("\n")

#     shutil.rmtree(PATH_SPEAKERS)
#     return final_speakers


# def read_file(file_name, sample_rate):
#     with wave.open(file_name, mode="rb") as wav_file:
#         channels = wav_file.getnchannels()
#         sample_width = wav_file.getsampwidth()
#         num_frames = wav_file.getnframes()

#         if wav_file.getframerate() != sample_rate:
#             raise ValueError(
#                 "Audio file should have a sample rate of %d. got %d" % (sample_rate, wav_file.getframerate()))
#         if sample_width != 2:
#             raise ValueError("Audio file should be 16-bit. got %d" % sample_width)
#         if channels == 2:
#             print("Eagle processes single-channel audio but stereo file is provided. Processing left channel only.")

#         samples = wav_file.readframes(num_frames)

#     frames = struct.unpack('h' * num_frames * channels, samples)

#     return frames[::channels]


def find_speakers(transcript, audio_object, audio_id):

    founded_speakers = {}

    try: 
        # audio_obj = AudioModel.query.get(audio_id)
        audio_filename = audio_helper.get_basename(audio_object.path)

        # transcribe_json = transcript["results"]
        transcribe_json = transcript
        # print("transcribe_json", transcribe_json)

        audio_obj,extension = audio_helper.create_audio_segment_object(audio_filename)
        
        recognization_results = {}

        for segment in transcribe_json:
            recognization_results[segment['speaker']] = 'Unknown'

        for segment in transcribe_json:
            # segment['speaker_recognized'] = False
            # if isinstance(segment['speaker'], int):
            start = segment['from']
            end = segment['to']
            print(segment)
            if (end - start > 1) and recognization_results[segment['speaker']] == 'Unknown':

                voice_chunk = {
                    "from": segment['from'],
                    "to": segment['to']
                }

                trimmed_audio = audio_helper.trim_and_save_audio_from_chunk(audio_obj,audio_id,'wav',voice_chunk,audio_filename.split('.')[0], PATH_AUDIO_CLIPS)

                (rate, signal) = scipy.io.wavfile.read(trimmed_audio)

                # print(rate, signal)

                extracted_features = extract_features(rate, signal)

                # ------------------------------------------------------------------------------------------------------------------------------------#
                #                                                          Loading the Gaussian Models                                                #
                # ------------------------------------------------------------------------------------------------------------------------------------#

                speakers = get_all_filename_from_folder(PATH_SPEAKER_RECOGNITION)
                
                gmm_models = []

                for user in speakers:
                    gmm_speaker = os.path.join(PATH_SPEAKER_RECOGNITION, user)
                    gmm_models.append(gmm_speaker)

                # gmm_models = [os.path.join('Models/', user)
                #                 for user in os.listdir('Models/')
                #                 if user.endswith('.gmm')]

                print("GMM Models : " + str(gmm_models))

                # Load the Gaussian user Models
                models = [pickle.load(open(user, 'rb')) for user in gmm_models]

                user_list = [user.split("/")[-1].split(".gmm")[0]
                for user in gmm_models]

                log_likelihood = numpy.zeros(len(models))

                print("log_likelihood>>>>", log_likelihood)

                for i in range(len(models)):
                    gmm = models[i]  # checking with each model one by one
                    # print(gmm)
                    scores = numpy.array(gmm.score(extracted_features))
                    # print("scores>>>>>>", scores)
                    log_likelihood[i] = scores.sum()

                print("Log liklihood : " + str(log_likelihood))

                numbers = str(log_likelihood).strip('[]').split()

                float_array = [float(num) for num in numbers]

                print("float_array>>>", float_array)
                identified_user_index = np.argmax([likelihood > -27.5 for likelihood in float_array])

                # First check the indexes greater then 30
                indexes_greater_than_minus_30 = [index for index, likelihood in enumerate(float_array) if likelihood > -30]
                
                print("indexes_greater_than_minus_30>>>>", indexes_greater_than_minus_30)

                if indexes_greater_than_minus_30:

                    if len(indexes_greater_than_minus_30) > 1:
                        indexes_greater_than_minus_25 = [index for index, likelihood in enumerate(float_array) if likelihood > -25]
                        
                        if indexes_greater_than_minus_25:
                            identified_user = max(indexes_greater_than_minus_25, key=lambda i: float_array[i])
                        
                        else:
                            identified_user = None        

                    else:
                        print("In this condition")
                        if float_array[indexes_greater_than_minus_30[0]] > -27.5:
                            identified_user = indexes_greater_than_minus_30[0]
                
                else:
                    identified_user = None

                # identified_user = None if indexes_greater_than_minus_25.length > 0 max(indexes_greater_than_minus_25, key=lambda i: float_array[i])

                # print("greatest_index>>>>", greatest_index)

                # print("identified_user_index>>>>", identified_user_index)

                # identified_user = None if float_array[identified_user_index] <= -25 else identified_user_index

                print(identified_user)

                auth_message = ""

                if identified_user is not None and user_list[identified_user]:
                    print("[ * ] You have been authenticated!")

                    speaker_id = user_list[identified_user].split('.')[0].split('-')[1]
                    # segment['speaker_recognized'] = True
                    speaker_id1 = int(speaker_id)
                    attendee = AttendeeModel.find_by_id(int(speaker_id1))
                    print("attendee", attendee)
                    if attendee is not None:
                        print("Heree")
                        recognization_results[segment["speaker"]] = attendee.json()
                    else:
                        recognization_results[segment["speaker"]] = "Unknown"
                    auth_message = "success"
                else:
                    print("[ * ] Sorry you have not been authenticated")
                    recognization_results[segment["speaker"]] = "Unknown"
                    auth_message = "fail"

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

        print("recognization_results>>>>>",recognization_results)
        return recognization_results


def calculate_delta(array):
    """Calculate and returns the delta of given feature vector matrix
    (https://appliedmachinelearning.blog/2017/11/14/spoken-speaker-identification-based-on-gaussian-mixture-models-python-implementation/)"""

    print("[Delta] : Calculating delta")

    rows, cols = array.shape
    deltas = numpy.zeros((rows, 20))
    N = 2
    for i in range(rows):
        index = []
        j = 1
        while j <= N:
            if i-j < 0:
                first = 0
            else:
                first = i-j
            if i+j > rows - 1:
                second = rows - 1
            else:
                second = i+j
            index.append((second, first))
            j += 1
        deltas[i] = (array[index[0][0]]-array[index[0][1]] +
                     (2 * (array[index[1][0]]-array[index[1][1]]))) / 10
    return deltas


def extract_features(rate, signal):
    print("[extract_features] : Exctracting featureses ...")

    mfcc_feat = mfcc(signal,
                     rate,
                     winlen=0.020,  # remove if not requred
                     preemph=0.95,
                     numcep=20,
                     nfft=1024,
                     ceplifter=15,
                     highfreq=6000,
                     nfilt=55,

                     appendEnergy=False)

    mfcc_feat = preprocessing.scale(mfcc_feat)

    delta_feat = calculate_delta(mfcc_feat)

    combined_features = numpy.hstack((mfcc_feat, delta_feat))

    return combined_features


def create_features(audio_path):
    # Load audio file
    y, sr = librosa.load(audio_path)
    # Extract MFCC features
    mfcc = librosa.feature.mfcc(y=y, sr=sr)
    # Mean pooling along the time axis
    mfcc_mean = np.mean(mfcc, axis=1)
    return mfcc_mean


def speaker_match(audio_path_1, audio_path_2):
    # Extract features from both audio samples
    features_1 = create_features(audio_path_1)
    features_2 = create_features(audio_path_2)
    ## Compute Euclidean distance
    distance = euclidean(features_1, features_2)
    # Normalize distance
    normalized_distance = distance / len(features_1)
    # Invert distance to obtain similarity score
    similarity = 1 - normalized_distance
    return similarity


def match_speakers(transcript, audio_object, audio_id):
    try: 
        audio_filename = audio_helper.get_basename(audio_object.path)

        # transcribe_json = transcript["results"]
        transcribe_json = transcript
        # print("transcribe_json", transcribe_json)

        audio_obj,extension = audio_helper.create_audio_segment_object(audio_filename)
        all_voice_samples = get_all_filename_from_folder(PATH_ATTENDEE_VOICE_SAMPLE)

        for segment in transcribe_json:
            # segment['speaker_recognized'] = False
            # if isinstance(segment['speaker'], int):
            start = segment['from']
            end = segment['to']
            print(segment)
            if (end - start > 1):

                voice_chunk = {
                    "from": segment['from'],
                    "to": segment['to']
                }

                trimmed_audio = audio_helper.trim_and_save_audio_from_chunk(audio_obj,audio_id,'wav',voice_chunk,audio_filename.split('.')[0], PATH_AUDIO_CLIPS)

                for voice_sample in all_voice_samples:
                    voice_file = get_all_filename_from_folder(os.path.join(PATH_ATTENDEE_VOICE_SAMPLE, voice_sample))
                    cur_voice_file = os.path.join(PATH_ATTENDEE_VOICE_SAMPLE, voice_sample, voice_file[0])
                    similarity = speaker_match(trimmed_audio, cur_voice_file)
                    print(f"Similarity {voice_sample}: {similarity}")


    except Exception as e:
        print("Error :", e)


if __name__ == "__main__":
    recognize()
