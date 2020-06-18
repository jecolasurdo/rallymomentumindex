
import hashlib
from contextlib import contextmanager
import signal
import sys


def first(items):
    return items[0] if len(items) > 0 else ""


def hash(s):
    return hashlib.md5(s.encode('utf-8')).hexdigest()


def prush(*args):
    print(*args)
    sys.stdout.flush()


@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutError("Timed out!")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
