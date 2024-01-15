import os
import urllib.request

# EXTERNAL_IP = urllib.request.urlopen('https://ident.me').read().decode('utf8')
EXTERNAL_IP = urllib.request.urlopen('https://api.ipify.org/').read().decode('utf8')
# EXTERNAL_IP = '192.168.1.7'
PORT = 5002
HOST = 'http://{}:{}'.format(EXTERNAL_IP, PORT)
BASE_URL_AUDIO_FILE = '{}/audio-file'.format(HOST)

MEETING_FOLDER = "meeting_audio_files"
MEETING_FOLDER_EDIT = "meeting_audio_files/edit"
SPEAKER_FOLDER = 'speaker'
CORPUS_FOLDER = "corpus_text_files"
UPDATED_TRANSCRIBE_FOLDER = "updated_transcribe_text_files"

PATH_PKG = os.path.dirname(os.path.abspath(__file__))
PATH_AUDIO = os.path.join(PATH_PKG, "static/audios")
PATH_FILES = os.path.join(PATH_PKG, "static/files")

PATH_FILES_CORPUS = os.path.join(PATH_FILES, CORPUS_FOLDER)
PATH_FILES_UPDATED_TRANSCRIBE = os.path.join(PATH_FILES, UPDATED_TRANSCRIBE_FOLDER)

PATH_AUDIO_CLIPS = os.path.join(PATH_AUDIO, "audio_clips")

PATH_ENV = os.path.join(PATH_PKG, ".env")
PATH_JSON = os.path.join(PATH_PKG, "static/json")
PATH_JSON_MEETING = os.path.join(PATH_JSON, MEETING_FOLDER)
PATH_JSON_MEETING_EDIT = os.path.join(PATH_JSON, MEETING_FOLDER_EDIT)
PATH_ATTENDEE_VOICE_SAMPLE = os.path.join(PATH_AUDIO, "attendee_voice_samples")
PATH_SPEAKER_RECOGNITION = os.path.join(PATH_AUDIO, "speaker")
PATH_SPEAKERS = os.path.join(PATH_AUDIO, "speakers")
PATH_EMBEDDING = os.path.join(PATH_PKG,"static/embedding")

if not os.path.exists(PATH_JSON):
    os.makedirs(PATH_JSON)

if not os.path.exists(PATH_JSON_MEETING):
    os.makedirs(PATH_JSON_MEETING)

if not os.path.exists(PATH_JSON_MEETING_EDIT):
    os.makedirs(PATH_JSON_MEETING_EDIT)
    
if not os.path.exists(PATH_FILES):
    os.makedirs(PATH_FILES)

if not os.path.exists(PATH_FILES_CORPUS):
    os.makedirs(PATH_FILES_CORPUS)

if not os.path.exists(PATH_FILES_UPDATED_TRANSCRIBE):
    os.makedirs(PATH_FILES_UPDATED_TRANSCRIBE)

if not os.path.exists(PATH_ATTENDEE_VOICE_SAMPLE):
    os.makedirs(PATH_ATTENDEE_VOICE_SAMPLE)

if not os.path.exists(PATH_SPEAKER_RECOGNITION):
    os.makedirs(PATH_SPEAKER_RECOGNITION)

if not os.path.exists(PATH_EMBEDDING):
    os.makedirs(PATH_EMBEDDING)
