from flask_restful import Resource
from flask import request
from speech_tagging.models.meeting import MeetingModel
from speech_tagging.models.attendee import AttendeeModel
from speech_tagging.commons.messages import *
from speech_tagging.schemas.recognize_speaker import RecognizeSpeakerSchema
from speech_tagging.watson_speech import json_helper
from speech_tagging.definitions import PATH_JSON_MEETING, PATH_SPEAKER_RECOGNITION, PATH_AUDIO_CLIPS
from speech_tagging.commons import audio_helper
from speech_tagging.commons import recognition_helper
from speech_tagging.models.audio import AudioModel
from speech_tagging.commons.utils import get_all_filename_from_folder
import os
import shutil

import pveagle
import wave
import struct

speaker_schema = RecognizeSpeakerSchema()


class RecognizeSpeaker(Resource):
    def post(self,audio_id):
        """
        :param audio_id:
        :return:
        """
        # speaker_json = request.get_json()
        # speaker = speaker_schema.load(speaker_json)
        #
        # meeting_id = speaker.get("meeting_id")
        # meeting = MeetingModel.find_by_id(meeting_id)

        # audio_id = meeting.audio_id
        # print(audio_id)
        # print("===>",meeting)

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

        audio_obj = AudioModel.query.get(audio_id)
        audio_filename = audio_helper.get_basename(audio_obj.path)
        transcription_filename = audio_filename.split('.')[0] + '.json'

        all_transribe_files = get_all_filename_from_folder(PATH_JSON_MEETING)
        print(PATH_JSON_MEETING)

        if transcription_filename not in all_transribe_files:
            return {"message": AUDIO_TRANSCRIPTION_DOESNOT_EXIST.format(transcription_filename)}, 400

        try: 
            # print("audio FileName:::+++>>>>", audio_filename)

            json_filepath = os.path.join(PATH_JSON_MEETING, transcription_filename)

            transcribe_json = json_helper.read_json(json_filepath)["results"]
            # print("transcribe_json", transcribe_json)
            audio_object,extension = audio_helper.create_audio_segment_object(audio_filename)
            
            recognization_results = []

            for segment in transcribe_json:
                start = segment['from']
                end = segment['to']
                if (end - start > 1):
                    # Speaker Profiles 
                    all_speakers = get_all_filename_from_folder(PATH_SPEAKER_RECOGNITION)

                    print(all_speakers)

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
                        access_key=os.environ.get("PICOVOICE_KEY"),
                        speaker_profiles=speaker_profiles)

                    voice_chunk = {
                        "from": segment['from'],
                        "to": segment['to']
                    }
                    print(voice_chunk)
                    print(audio_object)
                    trimmed_audio = audio_helper.trim_and_save_audio_from_chunk(audio_object,audio_id,'wav',voice_chunk,audio_filename.split('.')[0], PATH_AUDIO_CLIPS)
                    
                    try:
                        print("HERE")
                        audio = read_file(trimmed_audio, eagle.sample_rate)
                        # print("Eagle Sample Rate on Matching :", eagle.sample_rate)
                        # print(audio)
                        num_frames = len(audio) // eagle.frame_length
                        frame_to_second = eagle.frame_length / eagle.sample_rate
                        total_scores = 0
                        print(num_frames)
                        speaker_index = 0
                        for i in range(num_frames):
                            frame = audio[i * eagle.frame_length:(i + 1) * eagle.frame_length]
                            scores = eagle.process(frame)
                            time = i * frame_to_second
                            # print("Score>>>>>>>>", scores)
                            for num in scores:
                                if num > 0.5:
                                    total_scores = total_scores + 1
                                    speaker_index = scores.index(num)
                            # if 1.0 in scores:
                            #     total_scores = total_scores + 1
                        
                        print(total_scores)
                        print(speaker_index)

                        if ((total_scores * 100) / num_frames > 60):
                            print("speaker matched >>>>>>>", all_speakers[speaker_index])
                        else:
                            print("speaker not matched >>>>>>>>")

                    except pveagle.EagleActivationLimitError:
                        print('AccessKey has reached its processing limit.')
                    except pveagle.EagleError as e:
                        print("Failed to process audio: ", e)
                        raise
                    finally:
                        eagle.delete()
        
        except Exception as e:
            print("Error :", e)

        finally:
            clips_folder_path = os.path.join(PATH_AUDIO_CLIPS, str(audio_id))
            all_speaker_audio_clips = get_all_filename_from_folder(PATH_AUDIO_CLIPS)
            if audio_id in all_speaker_audio_clips:
                all_audio_clips_files = get_all_filename_from_folder(clips_folder_path)
                for audio_clip in all_audio_clips_files: 
                    audio_clip_path = os.path.join(clips_folder_path, audio_clip)
                    os.remove(audio_clip_path)
                os.rmdir(clips_folder_path)



