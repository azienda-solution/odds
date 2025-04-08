# -*- coding: utf-8 -*-
"""
Python & command-line tool to gather text on the Web:
web crawling/scraping, extraction of text, metadata, comments.
"""





from .core import bare_extraction, baseline, extract, html2txt, process_record
from .downloads import fetch_response, fetch_url
from .metadata import extract_metadata
from .utils import load_html

