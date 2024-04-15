import glob
import os
import time
from src.speech_tagging.definitions import PATH_AUDIO, PATH_JSON, PATH_FILES
import numpy as np


def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        if 'log_time' in kw:
            name = kw.get('log_name', method.__name__.upper())
            kw['log_time'][name] = int((te - ts) * 1000)
        else:
            print('%r  %2.2f ms' % (method.__name__, (te - ts) * 1000))
        return result

    return timed

def str2np(encoding):
    """Convert string of numpy to numpy array"""
    array = np.fromstring(encoding, dtype=np.int16)

    return array


def get_all_filename_from_folder(folder, root=PATH_AUDIO):
    """

    :param folder:
    :return:
    """
    fullpath = os.path.join(root,folder)
    files = glob.glob(fullpath + "/**")
    filenames = [os.path.basename(path) for path in files]
    return filenames

def get_all_jsonfile_from_folder(folder, root=PATH_JSON):
    """

    :param folder:
    :return:
    """
    fullpath = os.path.join(root,folder)
    files = glob.glob(fullpath + "/**")
    filenames = [os.path.basename(path) for path in files]
    return filenames

def get_all_textfile_from_folder(folder, root=PATH_FILES):
    """

    :param folder:
    :return:
    """
    fullpath = os.path.join(root,folder)
    files = glob.glob(fullpath + "/**")
    filenames = [os.path.basename(path) for path in files]
    return filenames


def get_all_filepaths(folder, root=PATH_AUDIO):
    """
    :param folder:
    :return:
    """
    fullpath = os.path.join(root,folder)
    files = glob.glob(fullpath + "/**")
    return files

def get_all_json_filepaths(folder, root=PATH_JSON):
    """
    :param folder:
    :return:
    """
    fullpath = os.path.join(root,folder)
    files = glob.glob(fullpath + "/**")
    return files


if __name__ == "__main__":
    get_all_filename_from_folder("meeting_audio_files")