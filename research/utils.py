
import hashlib
import os
import os.path
import signal
import sys
from contextlib import contextmanager


def first(items):
    return items[0] if len(items) > 0 else ""


def hash(s):
    return hashlib.md5(s.encode('utf-8')).hexdigest()


def prush(*args):
    print(*args)
    sys.stdout.flush()


class TimeoutException(Exception): pass

@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)


def pathto(base_path, *args):
    return os.path.join(os.getcwd(), base_path, *args)
