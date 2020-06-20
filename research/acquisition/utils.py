
import hashlib
import sys


def first(items):
    return items[0] if len(items) > 0 else ""


def hash(s):
    return hashlib.md5(s.encode('utf-8')).hexdigest()


def prush(*args):
    print(*args)
    sys.stdout.flush()
