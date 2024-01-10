import os

PATH_PKG = os.path.dirname(os.path.abspath(__file__))

#Constants For Speech Identification
# Signal processing
SAMPLE_RATE = 16000
PREEMPHASIS_ALPHA = 0.97
FRAME_LEN = 0.025
FRAME_STEP = 0.01
NUM_FFT = 512
BUCKET_STEP = 1
MAX_SEC = 5
TOLORENCE = 0.35
FRAMES_PER_BUFFER = 1024
COST_METRIC = "cosine"  # euclidean or cosine
INPUT_SHAPE=(NUM_FFT,None,1)

PATH_DATA = os.path.join(PATH_PKG,"model")

WEIGHTS_FILE = os.path.join(PATH_DATA,"weights.h5")
