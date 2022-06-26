"""
Pulls and pushes data to files
"""
import os
from os import listdir
from os.path import isfile, join


def get_files(path):
    """Returns all files in given path"""
    return [f for f in listdir(path) if isfile(join(path, f))]


def get_game_root():
    """Gets the path to the root folder of the game"""

    path = os.getcwd().replace("\\", "/")
    #     # Running from compiled source
    #     path = path[:path.rfind("/")]

    return path + "/"


def check_path(path):
    """Recreates folder if missing"""

    full_path = ""
    for part in path.split("/"):
        if "." not in part:
            full_path += part + "/"
            if not os.path.exists(full_path):
                print(part + " folder missing, recreating")
                os.mkdir(full_path)
        else:
            if not part in get_files(full_path):
                print(part + " file missing, recreating")
                open(full_path + part, "w").close()
            full_path += part
    return full_path
