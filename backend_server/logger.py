import sys
import re
import threading  # 新增

from utils import *


class Logger(object):
    def __init__(self, log_file):
        self.terminal = sys.stdout  # 保存原来的标准输出流
        self.log = open(log_file, "w", encoding="utf-8")  # 打开日志文件
        self.lock = threading.Lock()  # 新增

    def write(self, message):
        with self.lock:  # 新增
            self.terminal.write(message)  # 输出到终端
            clean_message = self.remove_ansi_escape(message)
            self.log.write(clean_message)  # 写入到日志文件

    def flush(self):
        with self.lock:  # 新增
            self.terminal.flush()
            self.log.flush()

    @staticmethod
    def remove_ansi_escape(message):
        """移除 ANSI 转义序列"""
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        return ansi_escape.sub("", message)


def init_logger(log_file):
    sys.stdout = Logger(log_file)
