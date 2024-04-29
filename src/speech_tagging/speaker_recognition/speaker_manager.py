import os
import numpy as np
from speech_tagging.speaker_recognition.model import vggvox_model
from speech_tagging.speaker_recognition.wav_reader import get_fft_spectrum, get_fft_spectrum_wav
from speech_tagging.speaker_recognition import definitions as c
import time
from scipy.spatial.distance import cdist
import tensorflow as tf

# graph = tf.get_default_graph()

graph = tf.compat.v1.get_default_graph()



class SpeakerIdentificationManager:

    def __init__(self):
        self.model = vggvox_model()
        # with graph.as_default():
        self.model.load_weights(c.WEIGHTS_FILE)

        self.embeddings = []
        self.speakers = []

    def verify_from_speech_array(self,speech_array):
        """

        :param speech_array:
        :return:
        """
        embedding = self.get_embeddings_from_list_file(audio=speech_array)
        id, dist = self.best_speaker_match(self.embeddings, embedding, tolerance=c.TOLORENCE)

        if id is None:
            print("Speaker: {} , distance: {}".format("Unknown", dist))
        else:
            print("Speaker: {} , distance: {}".format(self.speakers[id], dist))

        return self.speakers[id]

    def build_buckets(self,max_sec, step_sec, frame_step):
        """

        :param max_sec:
        :param step_sec:
        :param frame_step:
        :return:
        """
        buckets = {}
        frames_per_sec = int(1 / frame_step)
        end_frame = int(max_sec * frames_per_sec)
        step_frame = int(step_sec * frames_per_sec)
        for i in range(0, end_frame + 1, step_frame):
            s = i
            s = np.floor((s - 7 + 2) / 2) + 1  # conv1
            s = np.floor((s - 3) / 2) + 1  # mpool1
            s = np.floor((s - 5 + 2) / 2) + 1  # conv2
            s = np.floor((s - 3) / 2) + 1  # mpool2
            s = np.floor((s - 3 + 2) / 1) + 1  # conv3
            s = np.floor((s - 3 + 2) / 1) + 1  # conv4
            s = np.floor((s - 3 + 2) / 1) + 1  # conv5
            s = np.floor((s - 3) / 2) + 1  # mpool5
            s = np.floor((s - 1) / 1) + 1  # fc6
            if s > 0:
                buckets[i] = int(s)
        return buckets

    def get_embeddings_from_list_file(self,audio, max_sec=c.MAX_SEC):
        """

        :param filepath:
        :param max_sec:
        :return:
        """
        buckets = self.build_buckets(max_sec, c.BUCKET_STEP, c.FRAME_STEP)
        fft = get_fft_spectrum(audio, buckets)
        embedding = np.squeeze(self.model.predict(fft.reshape(1, *fft.shape, 1)))
        return embedding

    def get_embeddings_from_wav(self,filepath, max_sec=c.MAX_SEC):
        """

        :param filepath:
        :param max_sec:
        :return:
        """
        global graph

        buckets = self.build_buckets(max_sec, c.BUCKET_STEP, c.FRAME_STEP)
        fft = get_fft_spectrum_wav(filepath, buckets)

        # with graph.as_default():
        embedding = np.squeeze(self.model.predict(fft.reshape(1, *fft.shape, 1)))
        return embedding

    def find_distance(self, speech_encodings, speech_to_compare):
        """
        """
        return cdist(speech_encodings, speech_to_compare, metric=c.COST_METRIC) if len(speech_encodings) > 0 else None
        # return np.linalg.norm(speech_encodings - speech_to_compare, axis=1) if len(speech_encodings) > 0 else None

    def best_speaker_match(self, speech_encodings, speech_to_compare, tolerance):
        """
        :return:
        """
        tolerance = 10
        distances = self.find_distance(speech_encodings, [speech_to_compare])
        if distances is not  None:
            min_dist = min(distances)
            if min_dist < tolerance:
                return np.where(distances == min_dist)[0][0], min_dist

            return None, min_dist
        else:
            return None, None


if __name__ == "__main__":
    sim = SpeakerIdentificationManager()
