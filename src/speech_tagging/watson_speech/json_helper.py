import json


def read_json(path):
    """

    :param path:
    :return:
    """
    with open(path, "r") as read_file:
        data = json.load(read_file)
    return data

def write_json(path,data):
    """

    :param path,data:
    :return:
    """
    with open(path, "w") as write_file:
        json.dump(data,write_file)
    return True


def get_field_from_json(data,field):
    """

    :return:
    """
    return data.get(field)

def speaker_summarize(data_chunk):
    """

    :param data_chunk:
    :return:
    """
    final_chunk = []
    for chunk in data_chunk:
        speaker = chunk[0].get("speaker")
        start = chunk[0].get("from")
        end = chunk[-1].get("to")
        chunk_json = {"speaker":speaker,
                    "start":start,
                    "end":end
                        }
        final_chunk.append(chunk_json)

    return final_chunk


def speaker_change_detection(data):
    """

    :return:
    """
    speaker_prev = None
    i = 0
    i_prev = 0

    speaker_chunk = []

    for i,speaker_json in enumerate(data):
        speaker = speaker_json.get("speaker")

        if speaker_prev is not None:
            if speaker_prev == speaker:
                pass
            else:
                speaker_chunk.append(data[i_prev:i])
                i_prev = i

        speaker_prev = speaker

    if i_prev < i:
        speaker_chunk.append(data[i_prev:i])

    return speaker_chunk


def pipeline(path):
    """
    Chunk small continuous transcript of a speaker
    :param path:
    :return:
    """
    data = read_json(path=path)
    speaker = get_field_from_json(data, "results")
    # chunk = speaker_change_detection(speaker)
    # final_chunk = speaker_summarize(speaker)
    return speaker

def get_speaker_speak_time(speaker,json_path):
    """

    :param speaker:
    :return:
    """
    speaker_chunks = pipeline(json_path)
    speaker_time = []
    for speaker_chunk in speaker_chunks:
        if speaker_chunk['speaker'] == speaker:
            speaker_time.append(speaker_chunk)
    return speaker_time


if __name__ == "__main__":
   chunk = pipeline(path = "/home/bis/Projects/Project_upwork/Matt/speech-tagging/speech_tagging/static/json/meeting_audio_files/heuju_31.json")
   print(chunk)
