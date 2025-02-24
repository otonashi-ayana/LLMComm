import csv
import shutil, errno
from _ctypes import PyObj_FromPtr
import json
import re


class NoIndent(object):
    """Value wrapper."""

    def __init__(self, value):
        self.value = value


class MyEncoder(json.JSONEncoder):
    FORMAT_SPEC = "@@{}@@"
    regex = re.compile(FORMAT_SPEC.format(r"(\d+)"))

    def __init__(self, **kwargs):
        # Save copy of any keyword argument values needed for use here.
        self.__sort_keys = kwargs.get("sort_keys", None)
        super(MyEncoder, self).__init__(**kwargs)

    def default(self, obj):
        return (
            self.FORMAT_SPEC.format(id(obj))
            if isinstance(obj, NoIndent)
            else super(MyEncoder, self).default(obj)
        )

    def encode(self, obj):
        format_spec = self.FORMAT_SPEC  # Local var to expedite access.
        json_repr = super(MyEncoder, self).encode(obj)  # Default JSON.

        # Replace any marked-up object ids in the JSON repr with the
        # value returned from the json.dumps() of the corresponding
        # wrapped Python object.
        for match in self.regex.finditer(json_repr):
            # see https://stackoverflow.com/a/15012814/355230
            id = int(match.group(1))
            no_indent = PyObj_FromPtr(id)
            json_obj_repr = json.dumps(no_indent.value, sort_keys=self.__sort_keys)

            # Replace the matched id string with json formatted representation
            # of the corresponding Python object.
            json_repr = json_repr.replace(
                '"{}"'.format(format_spec.format(id)), json_obj_repr
            )

        return json_repr


def print_c(*args, sep=" ", end="\n", COLOR="purple", RESET="\033[0m"):
    if COLOR == "purple":
        COLOR = "\033[35m"
    elif COLOR == "blue":
        COLOR = "\033[94m"
    print(f"{COLOR}{sep.join(map(str, args))}{RESET}", end=end)


def copyanything(src, dst):
    """
    Copy over everything in the src folder to dst folder.
    ARGS:
      src: address of the source folder
      dst: address of the destination folder
    RETURNS:
      None
    """
    try:
        shutil.copytree(src, dst)
    except OSError as exc:  # python >2.5
        if exc.errno in (errno.ENOTDIR, errno.EINVAL):
            shutil.copy(src, dst)
        else:
            raise


def check_if_file_exists(curr_file):
    """
    Checks if a file exists
    ARGS:
      curr_file: path to the current csv file.
    RETURNS:
      True if the file exists
      False if the file does not exist
    """
    try:
        with open(curr_file) as f_analysis_file:
            pass
        return True
    except:
        return False


def read_file_to_list(curr_file, header=False, strip_trail=True):
    """
    Reads in a csv file to a list of list. If header is True, it returns a
    tuple with (header row, all rows)
    ARGS:
      curr_file: path to the current csv file.
    RETURNS:
      List of list where the component lists are the rows of the file.
    """
    if not header:
        analysis_list = []
        with open(curr_file, encoding="utf-8") as f_analysis_file:
            data_reader = csv.reader(f_analysis_file, delimiter=",")
            for count, row in enumerate(data_reader):
                if strip_trail:
                    row = [i.strip() for i in row]
                analysis_list += [row]
        return analysis_list
    else:
        analysis_list = []
        with open(curr_file, encoding="utf-8") as f_analysis_file:
            data_reader = csv.reader(f_analysis_file, delimiter=",")
            for count, row in enumerate(data_reader):
                if strip_trail:
                    row = [i.strip() for i in row]
                analysis_list += [row]
        return analysis_list[0], analysis_list[1:]


def read_2d_csv_to_list(curr_file):
    analysis_list = []
    with open(curr_file) as f_analysis_file:
        data_reader = csv.reader(f_analysis_file, delimiter=",")
        analysis_list = list(data_reader)
    return analysis_list


if __name__ == "__main__":
    pass
