import feedparser
from datetime import datetime
import pytz
import html


class RSSReader:
    def __init__(self, feed_url, ):
        """Initialize the RSS reader."""
        self.feed_url = None
        self.feed_data = None

    def load_feed(self, url):
        self.feed_url = url
        try:
            self.feed_data = feedparser.parse(url)
            return len(self.feed_data.entries) > 0
        except Exception as e:
            print(f"Error loading feed: {e}")
            return False

    def get_feed_info(self):
        """
        Get basic information about the feed.

        Returns:
            dict: Feed metadata including title, description, and link
        """
        if not self.feed_data:
            return None

        return {
            'title': self.feed_data.feed.get('title', 'No title'),
            'description': self.feed_data.feed.get('description', 'No description'),
            'link': self.feed_data.feed.get('link', ''),
            'last_updated': self.feed_data.feed.get('updated', 'No update date')
        }

    def get_entries(self, limit=None, sort_by_date=True):
        """
        Get feed entries, optionally limited and sorted.

        Args:
            limit (int, optional): Maximum number of entries to return
            sort_by_date (bool): Whether to sort entries by date

        Returns:
            list: List of feed entries as dictionaries
        """
        if not self.feed_data:
            return []

        entries = []
        for entry in self.feed_data.entries:
            # Clean and format the entry data
            clean_entry = {
                'title': html.unescape(entry.get('title', 'No title')),
                'link': entry.get('link', ''),
                'description': html.unescape(entry.get('description', 'No description')),
                'author': entry.get('author', 'Unknown author'),
                'published': entry.get('published', 'No publication date'),
                'updated': entry.get('updated', entry.get('published', 'No update date'))
            }

            # Try to parse and standardize the date
            try:
                date = entry.get('updated_parsed', entry.get('published_parsed'))
                if date:
                    clean_entry['timestamp'] = datetime(*date[:6], tzinfo=pytz.UTC)
            except (TypeError, ValueError):
                clean_entry['timestamp'] = None

            entries.append(clean_entry)

        # Sort entries by date if requested
        if sort_by_date:
            entries.sort(key=lambda x: x['timestamp'] if x['timestamp'] else datetime.min.replace(tzinfo=pytz.UTC),
                         reverse=True)

        # Apply limit if specified
        if limit:
            entries = entries[:limit]

        return entries

    def search_entries(self, keyword, case_sensitive=False):
        """
        Search for entries containing the given keyword.

        Args:
            keyword (str): Keyword to search for
            case_sensitive (bool): Whether to perform case-sensitive search

        Returns:
            list: List of matching entries
        """
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
