import random
import string
import csv
import time
import datetime as dt
import pathlib
import os
import sys
import numpy
import math
import shutil, errno

from os import listdir


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


if __name__ == "__main__":
    pass
