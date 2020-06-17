# Contents of this directory

## raw_html/*
Directory containing html scraped from elephrame.com. Each file contains the html
rendered for a single page of results for the BLM protest listing at elephrame.

## extracted.json
Structured data extracted from the contents of the `raw_html` directory.
The data in this file has been structured into a JSON format, but has not been
otherwise cleaned/processed. It is a true representation of the data extracted
from the html of the elephrame website.

## cleaned.json
This is a cleaned dataset derived from `extracted.json`.

Fields:
 - Location: Same as extracted location with whitespace stripped.
 - Active: True if start or end date was listed as "Present", otherwise False.
 - Start: The start date in ISO format or None if date was listed as "Present".
 - End: The end date in ISO format or None if either no end date was specified or the end date was specified as "Present".
 - Subject: Same as extracted subject with whitespace stripped.
 - Magnitude: The "participants" estimate restated as an order of magnitude. Will be -1 if "Unclear" was specified. Will be -2 if the raw data could not be cleanly interpreted.
 - Timeframe: The "time of day" estimate from the extracted data restated as the estimated start time ("morning", "afternoon", "evening"). If a timespan was given ("morning-afternoon"), the first timeframe was taken to specify the general start time. Timeframes listed as "continuous" were re-interpretted as having started in the morning. Timeframes listed as "unclear" and timeframes with bad data are output as "unknown".
 - Description: Same as extracted description with whitespace stripped.
 - URLs: Each URL is expanded to two fields, "hash" and "URL". The hash field is an md5 hash of the URL which can be used to cross reference the URL against its codex data (see codex section below). The URL is is the same as the extracted URL with whitespace removed. Whitespace is removed before calculating the URL hash value.

## codex/*