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
This is a cleaned dataset derived from `extracted.json`. Some transformations
include:

 - Removing padding from text.
 - Standardizing date formats.
 - Standardizing the participant estimates.
 - Standardizing the "time of day" values.
 - A hash value for each URL (for cross referencing against the codex data)

Refer to `scraper.py`
for more details about the tranformations present in this file.

## codex/*
This directory contains a set of text documents, each 