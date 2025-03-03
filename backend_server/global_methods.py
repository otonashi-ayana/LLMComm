import csv
import shutil, errno


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
