from google import google
import urllib.request
import urllib.error
from textpipe import doc, pipeline


class Searcher:
    def __init__(self, keywords, num_page=1):
        self.keywords = keywords
        self.num_page = num_page

    def search(self):
        terms = " ".join(self.keywords)
        search_results = google.search(terms, self.num_page)
        for result in search_results:
            try:
                response = urllib.request.urlopen(result.link)
            except urllib.error.HTTPError:
                continue
            except urllib.error.URLError as e:
                continue
            document = doc.Doc(response.read())
            yield {
                "doctype": "website",
                "content": document.clean
            }
