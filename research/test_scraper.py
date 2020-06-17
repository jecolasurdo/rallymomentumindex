
import research.scraper as scraper
from datetime import datetime

def test__fmt_date():
    test_cases = [
        {
            "input": " - Thursday, July 6, 2016",
            "output": datetime(2016, 7, 6) 
        },
        {
            "input": "Thursday, July 6, 2016",
            "output": datetime(2016, 7, 6)
        },
        {
            "input": "",
            "output": None 
        },
    ]

    for test_case in test_cases:
        assert scraper._fmt_date(test_case["input"]) == test_case["output"]
