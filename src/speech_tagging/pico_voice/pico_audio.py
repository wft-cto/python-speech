from picovoice import Picovoice

ACCESS_KEY = 'Ygc7uEluQbKlt+OPC2G5XrNh+NhSWzToKepBChF4S5THx9w26vw3EQ==' 

access_key = "${ACCESS_KEY}" # AccessKey obtained from Picovoice Console (https://console.picovoice.ai/)

keyword_path = ...

def wake_word_callback():
    pass

context_path = ...

def inference_callback(inference):
    # `inference` exposes three immutable fields:
    # (1) `is_understood`
    # (2) `intent`
    # (3) `slots`
    pass

picovoice = Picovoice(
        access_key=access_key,
        keyword_path=keyword_path,
        wake_word_callback=wake_word_callback,
        context_path=context_path,
        inference_callback=inference_callback)