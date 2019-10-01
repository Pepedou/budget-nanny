import logging
import time
from contextlib import contextmanager

_logger = logging.getLogger(__name__)


@contextmanager
def timeit(name):
    time1 = time.time()
    yield
    time2 = time.time()

    ms = (time2 - time1) * 1000.0
    seconds = (ms / 1000) % 60
    seconds = int(seconds)
    minutes = (ms / (1000 * 60)) % 60
    minutes = int(minutes)
    hours = (ms / (1000 * 60 * 60)) % 24
    hours = int(hours)
    took_more_than_one_second = hours > 0 or minutes > 0 or seconds > 0

    if took_more_than_one_second:
        _logger.info('%s finished in %02d:%02d:%02d".' % (name, hours, minutes, seconds))
    else:
        _logger.info('{} finished in {:.3f} ms.'.format(name, ms))
