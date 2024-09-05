# -*- coding: utf-8 -*-
"""
Created on 2018-12-08 16:50
---------
@summary:
---------
@author: Boris
@email: boris_liu@foxmail.com
"""

import logging
import os
import sys
from logging.handlers import BaseRotatingHandler

import loguru
from better_exceptions import format_exception

# from feapder import 
# 日志
LOG_NAME = os.path.basename(os.getcwd())
LOG_PATH = "log/%s.log" % LOG_NAME  # log存储路径
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")  # 日志级别
LOG_COLOR = True  # 是否带有颜色
LOG_IS_WRITE_TO_CONSOLE = True  # 是否打印到控制台
LOG_IS_WRITE_TO_FILE = False  # 是否写文件
LOG_MODE = "w"  # 写文件的模式
LOG_MAX_BYTES = 10 * 1024 * 1024  # 每个日志文件的最大字节数
LOG_BACKUP_COUNT = 20  # 日志文件保留数量
LOG_ENCODING = "utf8"  # 日志文件编码
# 是否详细的打印异常
PRINT_EXCEPTION_DETAILS = True
# 设置不带颜色的日志格式
LOG_FORMAT = "%(threadName)s|%(asctime)s|%(filename)s|%(funcName)s|line:%(lineno)d|%(levelname)s| %(message)s"
# 设置带有颜色的日志格式
os.environ["LOGURU_FORMAT"] = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>line:{line}</cyan> | <level>{message}</level>"
)
OTHERS_LOG_LEVAL = "ERROR"  # 第三方库的log等级

class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Retrieve context where the logging call occurred, this happens to be in the 6th frame upward
        logger_opt = loguru.logger.opt(depth=6, exception=record.exc_info)
        logger_opt.log(record.levelname, record.getMessage())


# 重写 RotatingFileHandler 自定义log的文件名
# 原来 xxx.log xxx.log.1 xxx.log.2 xxx.log.3 文件由近及远
# 现在 xxx.log xxx1.log xxx2.log  如果backup_count 是2位数时  则 01  02  03 三位数 001 002 .. 文件由近及远
class RotatingFileHandler(BaseRotatingHandler):
    def __init__(
        self, filename, mode="a", max_bytes=0, backup_count=0, encoding=None, delay=0
    ):
        BaseRotatingHandler.__init__(self, filename, mode, encoding, delay)
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.placeholder = str(len(str(backup_count)))

    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None
        if self.backup_count > 0:
            for i in range(self.backup_count - 1, 0, -1):
                sfn = ("%0" + self.placeholder + "d.") % i  # '%2d.'%i -> 02
                sfn = sfn.join(self.baseFilename.split("."))
                # sfn = "%d_%s" % (i, self.baseFilename)
                # dfn = "%d_%s" % (i + 1, self.baseFilename)
                dfn = ("%0" + self.placeholder + "d.") % (i + 1)
                dfn = dfn.join(self.baseFilename.split("."))
                if os.path.exists(sfn):
                    # print "%s -> %s" % (sfn, dfn)
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)
            dfn = (("%0" + self.placeholder + "d.") % 1).join(
                self.baseFilename.split(".")
            )
            if os.path.exists(dfn):
                os.remove(dfn)
            # Issue 18940: A file may not have been created if delay is True.
            if os.path.exists(self.baseFilename):
                os.rename(self.baseFilename, dfn)
        if not self.delay:
            self.stream = self._open()

    def shouldRollover(self, record):
        if self.stream is None:  # delay was set...
            self.stream = self._open()
        if self.max_bytes > 0:  # are we rolling over?
            msg = "%s\n" % self.format(record)
            self.stream.seek(0, 2)  # due to non-posix-compliant Windows feature
            if self.stream.tell() + len(msg) >= self.max_bytes:
                return 1
        return 0


def get_logger(
    name=None,
    path=None,
    log_level=None,
    is_write_to_console=None,
    is_write_to_file=None,
    color=None,
    mode=None,
    max_bytes=None,
    backup_count=None,
    encoding=None,
    log_format=None
):
    """
    @summary: 获取log
    ---------
    @param name: log名
    @param path: log文件存储路径 如 D://xxx.log
    @param log_level: log等级 CRITICAL/ERROR/WARNING/INFO/DEBUG
    @param is_write_to_console: 是否输出到控制台
    @param is_write_to_file: 是否写入到文件 默认否
    @param color：是否有颜色
    @param mode：写文件模式
    @param max_bytes： 每个日志文件的最大字节数
    @param backup_count：日志文件保留数量
    @param encoding：日志文件编码
    ---------
    @result:
    """
    # 加载最新的值
    name = name or LOG_NAME
    path = path or LOG_PATH
    log_level = log_level or LOG_LEVEL
    is_write_to_console = (
        is_write_to_console
        if is_write_to_console is not None
        else LOG_IS_WRITE_TO_CONSOLE
    )
    is_write_to_file = (
        is_write_to_file
        if is_write_to_file is not None
        else LOG_IS_WRITE_TO_FILE
    )
    color = color if color is not None else LOG_COLOR
    mode = mode or LOG_MODE
    max_bytes = max_bytes or LOG_MAX_BYTES
    backup_count = backup_count or LOG_BACKUP_COUNT
    encoding = encoding or LOG_ENCODING

    # logger 配置
    name = name.split(os.sep)[-1].split(".")[0]  # 取文件名

    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    formatter = logging.Formatter(log_format or LOG_FORMAT)
    # if PRINT_EXCEPTION_DETAILS:
    formatter.formatException = lambda exc_info: format_exception(*exc_info)

    # 定义一个RotatingFileHandler，最多备份5个日志文件，每个日志文件最大10M
    if is_write_to_file:
        if path and not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))

        rf_handler = RotatingFileHandler(
            path,
            mode=mode,
            max_bytes=max_bytes,
            backup_count=backup_count,
            encoding=encoding,
        )
        rf_handler.setFormatter(formatter)
        logger.addHandler(rf_handler)
    if color and is_write_to_console:
        loguru_handler = InterceptHandler()
        loguru_handler.setFormatter(formatter)
        # logging.basicConfig(handlers=[loguru_handler], level=0)
        logger.addHandler(loguru_handler)
    elif is_write_to_console:
        stream_handler = logging.StreamHandler()
        stream_handler.stream = sys.stdout
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    _handler_list = []
    _handler_name_list = []
    # 检查是否存在重复handler
    for _handler in logger.handlers:
        if str(_handler) not in _handler_name_list:
            _handler_name_list.append(str(_handler))
            _handler_list.append(_handler)
    logger.handlers = _handler_list
    return logger


# logging.disable(logging.DEBUG) # 关闭所有log

# 不让打印log的配置
STOP_LOGS = [
    # ES
    "urllib3.response",
    "urllib3.connection",
    "elasticsearch.trace",
    "requests.packages.urllib3.util",
    "requests.packages.urllib3.util.retry",
    "urllib3.util",
    "requests.packages.urllib3.response",
    "requests.packages.urllib3.contrib.pyopenssl",
    "requests.packages",
    "urllib3.util.retry",
    "requests.packages.urllib3.contrib",
    "requests.packages.urllib3.connectionpool",
    "requests.packages.urllib3.poolmanager",
    "urllib3.connectionpool",
    "requests.packages.urllib3.connection",
    "elasticsearch",
    "log_request_fail",
    # requests
    "requests",
    "selenium.webdriver.remote.remote_connection",
    "selenium.webdriver.remote",
    "selenium.webdriver",
    "selenium",
    # markdown
    "MARKDOWN",
    "build_extension",
    # newspaper
    "calculate_area",
    "largest_image_url",
    "newspaper.images",
    "newspaper",
    "Importing",
    "PIL",
]

# 关闭日志打印
OTHERS_LOG_LEVAL = eval("logging." + OTHERS_LOG_LEVAL)
for STOP_LOG in STOP_LOGS:
    logging.getLogger(STOP_LOG).setLevel(OTHERS_LOG_LEVAL)

# print(logging.Logger.manager.loggerDict) # 取使用debug模块的name

# 日志级别大小关系为：CRITICAL > ERROR > WARNING > INFO > DEBUG


class Log:
    log = None

    def __init__(self,
        **kwargs
    ):
        self.kwargs = kwargs

    def func(self, log_level):
        def wrapper(msg, *args, **kwargs):
            if self.isEnabledFor(log_level):
                self._log(log_level, msg, args, **kwargs)

        return wrapper

    def __getattr__(self, name):
        # 调用log时再初始化，为了加载最新的setting
        
        if self.__class__.log is None:
            self.__class__.log = get_logger(**self.kwargs)
        return getattr(self.__class__.log, name)

    @property
    def debug(self):
        return self.__class__.log.debug

    @property
    def info(self):
        return self.__class__.log.info

    @property
    def success(self):
        log_level = logging.INFO + 1
        logging.addLevelName(log_level, "success".upper())
        return self.func(log_level)

    @property
    def warning(self):
        return self.__class__.log.warning

    @property
    def exception(self):
        return self.__class__.log.exception

    @property
    def error(self):
        return self.__class__.log.error

    @property
    def critical(self):
        return self.__class__.log.critical
