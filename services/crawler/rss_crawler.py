import pytz
import html
import feedparser
from datetime import datetime

import requests
import xml.etree.ElementTree as et
from urllib.parse import urlparse


def is_rss_feed(url):
    try:
        parsed_url = urlparse(url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            return False

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        content_type = response.headers.get('content-type', '').lower()
        if not any(valid_type in content_type for valid_type in ['application/rss+xml', 'application/xml', 'text/xml']):
            return False

        root = et.fromstring(response.content)
        rss_indicators = [
            'rss',
            'feed',
            'channel',
            'item',
            'entry'
        ]

        if root.tag in rss_indicators:
            return True

        for child in root:
            if child.tag in rss_indicators:
                return True
        return False
    except requests.RequestException:
        return False
    except et.ParseError:
        return False
    except Exception:
        return False

def load_feed(self, url):
    self.feed_url = url
    try:
        self.feed_data = feedparser.parse(url)
        return len(self.feed_data.entries) > 0
    except Exception as e:
        print(f"Error loading feed: {e}")
        return False

def get_feed_info(self):
    if not self.feed_data:
        return None

    return {
        'title': self.feed_data.feed.get('title', 'No title'),
        'description': self.feed_data.feed.get('description', 'No description'),
        'link': self.feed_data.feed.get('link', ''),
        'last_updated': self.feed_data.feed.get('updated', 'No update date')
    }

def get_entries(self, limit=None, sort_by_date=True):
    if not self.feed_data:
        return []

    entries = []
    for entry in self.feed_data.entries:
        clean_entry = {
            'title': html.unescape(entry.get('title', 'No title')),
            'link': entry.get('link', ''),
            'description': html.unescape(entry.get('description', 'No description')),
            'author': entry.get('author', 'Unknown author'),
            'published': entry.get('published', 'No publication date'),
            'updated': entry.get('updated', entry.get('published', 'No update date'))
        }
        try:
            date = entry.get('updated_parsed', entry.get('published_parsed'))
            if date:
                clean_entry['timestamp'] = datetime(*date[:6], tzinfo=pytz.UTC)
        except (TypeError, ValueError):
            clean_entry['timestamp'] = None

        entries.append(clean_entry)
    if sort_by_date:
        entries.sort(key=lambda x: x['timestamp'] if x['timestamp'] else datetime.min.replace(tzinfo=pytz.UTC),
                     reverse=True)
    if limit:
        entries = entries[:limit]

    return entries

def search_entries(self, keyword, case_sensitive=False):
    if not self.feed_data:
        return []

    matches = []
    entries = self.get_entries()

    for entry in entries:
        search_text = f"{entry['title']} {entry['description']}"
        if not case_sensitive:
            search_text = search_text.lower()
            keyword = keyword.lower()

        if keyword in search_text:
            matches.append(entry)

    return matches
