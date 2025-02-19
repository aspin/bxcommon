import logging
from typing import Type
from logging import LogRecord

from bxutils.logging.log_level import LogLevel

logger_class: Type[logging.Logger] = logging.getLoggerClass()
log_record_class: Type[LogRecord] = logging.getLogRecordFactory()  # pyre-ignore


class CustomLogRecord(log_record_class):
    def getMessage(self):
        msg = str(self.msg)
        if self.args:
            msg = msg.format(*self.args)
        return msg


class CustomLogger(logger_class):

    def debug(self, msg, *args, **kwargs):
        super(CustomLogger, self).debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        super(CustomLogger, self).info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        super(CustomLogger, self).warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        super(CustomLogger, self).error(msg, *args, **kwargs)

    def exception(self, msg, *args, exc_info=True, **kwargs):
        super(CustomLogger, self).exception(msg, *args, exc_info=exc_info, **kwargs)

    def critical(self, msg, *args, **kwargs):
        super(CustomLogger, self).critical(msg, *args, **kwargs)

    def log(self, level, msg, *args, **kwargs):
        super(CustomLogger, self).log(level, msg, *args, **kwargs)

    def fatal(self, msg, *args, exc_info=True, **kwargs):
        if self.isEnabledFor(LogLevel.FATAL):
            self.exception(msg, *args, exc_info=exc_info, **kwargs)

    def stats(self, msg, *args, **kwargs):
        if self.isEnabledFor(LogLevel.STATS):
            self._log(LogLevel.STATS, msg, args, kwargs)

    def statistics(self, msg, *args, **kwargs):
        self.stats(msg, *args, **kwargs)

    def trace(self, msg, *args, **kwargs):
        if self.isEnabledFor(LogLevel.TRACE):
            self._log(LogLevel.TRACE, msg, args, kwargs)

    def set_level(self, level):
        self.setLevel(level)

    def set_immediate_flush(self, flush_immediately: bool):
        pass
