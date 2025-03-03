import threading
import time
from utils import *
from logger import init_logger
import sys


def thread_function(name, logger):
    for i in range(5):
        logger.write(f"Thread {name} writing {i}\n")
        time.sleep(0.1)


if __name__ == "__main__":
    log_file = "test_log.txt"
    init_logger(log_file)

    threads = []
    for index in range(3):
        x = threading.Thread(target=thread_function, args=(index, sys.stdout))
        threads.append(x)
        x.start()

    for thread in threads:
        thread.join()

    print("Logging complete.")
