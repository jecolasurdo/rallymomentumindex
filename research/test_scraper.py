
import research.scraper as scraper
from datetime import datetime


def test__fmt_date():
    tt = [
        {
            "in": " - Thursday, July 6, 2016",
            "out": datetime(2016, 7, 6).isoformat()
        },
        {
            "in": "Thursday, July 6, 2016",
            "out": datetime(2016, 7, 6).isoformat()
        },
        {
            "in": "",
            "out": None
        },
        {
            "in": "Present",
            "out": None
        },
        {
            "in": " - Present",
            "out": None
        }
    ]

    for t in tt:
        assert scraper._fmt_date(t["in"]) == t["out"]


def test__fmt_participants():
    tt = [
        # Vague cases
        {
            "in": "Unclear # of demonstrators",
            "out": -1
        },
        {
            "in": "Varied demonstrators",
            "out": -1
        },
        # Long form magnitudes
        {
            "in": "Dozens of demonstrators",
            "out": 10
        },
        {
            "in": "Hundreds of demonstrators",
            "out": 100
        },
        {
            "in": "Thousands of demonstrators",
            "out": 1000
        },
        # Numeric estimates
        {
            "in": "1-3 demonstrators",
            "out": 1
        },
        {
            "in": "125 demonstrators",
            "out": 100
        },
        {
            "in": "12+ demonstrators",
            "out": 10
        },
        {
            "in": "100-150 demonstrators",
            "out": 100
        },
        {
            "in": "1000-2500 demonstrators",
            "out": 1000
        },
        {
            "in": "11000-15000 demonstrators",
            "out": 10000
        },
        # Garbage
        {
            "in": "TBD",
            "out": -2
        },
        {
            "in": " demonstrators",
            "out": -2
        },
        {
            "in": "random goop poipalkjsdkj",
            "out": -2
        }
    ]

    for t in tt:
        assert scraper._fmt_participants(t["in"]) == t["out"]
