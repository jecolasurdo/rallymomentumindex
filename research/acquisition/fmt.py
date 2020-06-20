import math
import re
from datetime import datetime

from research.acquisition import utils


def location(s):
    return s.strip()


def active(d):
    return True if d == "Present" else False


def date(d):
    if d[:3] == " - ":
        d = d[3:]
    if d in ["", "Present"]:
        return None
    return datetime.strptime(d, "%A, %B %d, %Y").isoformat()


def subject(s):
    return s.strip()


def participants(p):
    if "Unclear" in p:
        return -1
    if "Varied" in p:
        return -1
    if "Dozens" in p:
        return 10
    if "Hundreds" in p:
        return 100
    if "Thousands" in p:
        return 1000
    m = re.search(r'\d+', p)
    if m is not None:
        n = int(m.group(0))
        return 10 ** round(math.log(n, 10))
    return -2


def timeframe(t):
    t = t.strip().lower()
    if t.endswith(" (est.)"):
        t = t[:-7]
    if t in ["unclear", "unclar"]:
        return "unknown"
    if t in ["morning", "afternoon", "evening"]:
        return t
    if t in ["afterrnoon", "afternon", "aftermoon", "afternoon-evening", "afteroon-evening", "afternoon-morning"]:
        return "afternoon"
    if t == "evening-morning":
        return "evening"
    if t in ["morning-evening", "morning-afternoon", "continuous", "continous"]:
        return "morning"
    return "unknown"


def description(d):
    return d.strip()


def urls(urls):
    for url in urls:
        url = url.strip()
        yield {
            "hash": utils.hash(url),
            "url": url
        }
