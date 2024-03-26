#
#    Copyright 2018-2023 Picovoice Inc.
#
#    You may not use this file except in compliance with the license. A copy of the license is located in the "LICENSE"
#    file accompanying this source.
#
#    Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
#    an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
#    specific language governing permissions and limitations under the License.
#

from pvleopard import create, LeopardActivationLimitError
from tabulate import tabulate
from speech_tagging.models.audio import AudioModel
from speech_tagging.commons import audio_helper
from speech_tagging.definitions import MEETING_FOLDER, PATH_AUDIO
from speech_tagging.commons.extract_actions import ExtractAction
from speech_tagging.commons.entity_recognition import recognize_ents
import os


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
    # speaker_labels = transcript["speaker_labels"]
    # alternatives = transcript["results"]
    
    transcript_list = []
    transcript_text_list = []
    transcript_time_list = []
    # # for accessing each object of speaker_labels
    index = 0
    print(transcript[0])
    print(transcript[0].speaker_tag)
    initial_speaker = transcript[0].speaker_tag
    print("initial_speaker", initial_speaker)

    # timestamps = alternative_data["timestamps"]

    try:

        for timestamp,has_more in lookahead(transcript):  #timestamps
            # timestamp.append(speaker_labels[index]["speaker"])          
            if int(timestamp.speaker_tag) == initial_speaker:
                print("HERE First")
                   
                transcript_time_list.append(round(timestamp.start_sec, 2))
                transcript_time_list.append(round(timestamp.end_sec, 2))
                transcript_text_list.append(timestamp.word)
                print(transcript_text_list)
                # check whether is it last item of that loop
                if (has_more == False):
                    print("Last Stamp")
                    # print("last timestamp",timestamp[0])
                    transcript_text = " ".join(transcript_text_list) 
                    print(transcript_text)
                    transcript_text = transcript_text.replace("%HESITATION","")
                    transcript_text_original = transcript_text
                    if len(transcript_text) > 0:
                        # print(transcript_text)
                        # get action phrase from the transcripted text
                        action_phrase = ea.check_imperative(transcript_text)
                        print(action_phrase)
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

                    
            elif int(timestamp.speaker_tag) != initial_speaker:
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
                transcript_text_list.append(timestamp.word)
                
                transcript_time_list.append(round(timestamp.start_sec, 2))
                transcript_time_list.append(round(timestamp.end_sec, 2))
                initial_speaker = timestamp.speaker_tag
                
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

    except Exception as e:

        print("Error form format>>>>>>>>", e)
            
    return transcript_list


def getTranscribe(audio_id):

    audio_obj = AudioModel.find_by_id(audio_id)
    filename = audio_helper.get_basename(audio_obj.path)

    audio_path = os.path.join(PATH_AUDIO, MEETING_FOLDER, filename)

    print("Audio Path>>>>>>>>",audio_path)

    o = create(
        access_key=os.environ.get("PICOVOICE_KEY"),
        enable_automatic_punctuation=False,
        enable_diarization=True)

    try:
        transcript, words = o.process_file(audio_path)
        format_transcripts = format_transcript(words)
        print("format_transcripts>>>", format_transcripts)
        # print(words)
        # Convert the array to the desired format
        # result_list = []
        # current_speaker = None
        # current_vocal = ''
        # current_start_sec = None

        # for word_data in words:
        #     if current_speaker is None:
        #         current_speaker = word_data.speaker_tag
        #         current_start_sec = round(word_data.start_sec, 2)
        #         print(current_start_sec)

        #     if current_speaker == word_data.speaker_tag:
        #         current_vocal += word_data.word + ' '
        #     else:
        #         # Add the current segment to the result list
        #         # cur_start_sec = list(current_start_sec)
        #         # print(type(current_start_sec))
        #         result_list.append({
        #             "speaker": current_speaker,
        #             "from": current_start_sec,
        #             "to": round(word_data.start_sec, 2),
        #             "vocal": current_vocal.strip(),
        #             "action_phrase": []
        #         })

        #             # Start a new segment for the next speaker
        #         current_speaker = word_data.speaker_tag
        #         current_start_sec = round(word_data.end_sec, 2)
        #         current_vocal = word_data.word + ' '

        #     # Add the last segment to the result list
        # result_list.append({
        #     "speaker": current_speaker,
        #     "from": current_start_sec,
        #     "to": round(words[-1].end_sec, 2),
        #     "vocal": current_vocal.strip(),
        #     "action_phrase": []
        # })

        # print("results>>>>", result_list)

        return format_transcripts, 1

    except LeopardActivationLimitError:
        print('AccessKey has reached its processing limit.')