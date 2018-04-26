import logging


def _get_formatter():
    date_fmt = "%Y-%m-%d %H:%M:%S"
    log_fmt = '%(asctime)s %(levelname)s %(name)s:%(lineno)d %(message)s'

    formatter = logging.Formatter(log_fmt, date_fmt)
    return formatter


def getLogger(name):
    formatter = _get_formatter()
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger
