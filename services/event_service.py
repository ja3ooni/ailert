import logging
import feedparser
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from dbhandler import Event, sites

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class EventsService:
    def __init__(self, rss_feed_url=sites["events_feed"], html_links=sites["events_url"], top_n=3):
        self.rss_feed_url = rss_feed_url
        self.html_links = html_links  # Fixed variable name from html_link to html_links
        self.top_n = top_n
        self.events = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }

    def _get_events_from_rss_feed(self) -> List[Dict]:
        try:
            feed = feedparser.parse(self.rss_feed_url)
            if not feed.entries:
                logger.warning(f"No entries found in RSS feed: {self.rss_feed_url}")
                return []

            events = []
            for entry in feed.entries[:self.top_n]:
                event = {
                    "title": entry.get('title', ''),
                    "description": entry.get('description', ''),
                    "date": entry.get('published', ''),
                    "location": "",  # RSS feed might not have location
                    "engagement": 0
                }
                events.append(event)
            return events
        except Exception as e:
            logger.error(f"Error parsing RSS feed: {e}")
            return []

    def _get_events_from_html_link(self) -> List[Dict]:  # Fixed method name typo
        events = []
        for url in self.html_links:
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')

                if "conferencealerts" in url:
                    # Updated selector based on current site structure
                    events.extend(self._parse_conference_alerts(soup))
                elif "aideadlin.es" in url:
                    events.extend(self._parse_aideadlines(soup))

                if len(events) >= self.top_n:
                    return events[:self.top_n]
            except requests.RequestException as e:
                logger.error(f"Error fetching {url}: {e}")
                continue
            except Exception as e:
                logger.error(f"Error processing {url}: {e}")
                continue
        return events

    def _parse_conference_alerts(self, soup: BeautifulSoup) -> List[Dict]:
        events = []
        # Updated selectors based on current site structure
        items = soup.find_all('div', class_='conference-item')  # Changed from 'event-item'

        if not items:
            # Fallback to alternative selectors
            items = soup.find_all('div', class_='conf-item')

        for item in items:
            try:
                title_elem = item.find(['h2', 'h3', 'h4']) or item.find(class_='conf-title')
                date_elem = item.find(class_=['date', 'conf-date'])
                location_elem = item.find(class_=['location', 'conf-location'])
                desc_elem = item.find(class_=['description', 'conf-description'])

                if not title_elem:
                    continue

                event = {
                    "title": title_elem.text.strip(),
                    "date": date_elem.text.strip() if date_elem else "",
                    "location": location_elem.text.strip() if location_elem else "",
                    "description": desc_elem.text.strip() if desc_elem else "",
                    "engagement": 0  # Default value if not found
                }
                events.append(event)
            except Exception as e:
                logger.error(f"Error parsing conference alert item: {e}")
                continue
        return events

    def _parse_aideadlines(self, soup: BeautifulSoup) -> List[Dict]:
        events = []
        items = soup.select('.conference-item, .deadline-item')

        for item in items:
            try:
                title_elem = item.find(['h3', 'h4']) or item.select_one('.conf-title')
                date_elem = item.select_one('.deadline, .date')
                location_elem = item.select_one('.location, .venue')
                desc_elem = item.select_one('.description, .abstract')

                if not title_elem:
                    continue

                event = {
                    "title": title_elem.text.strip(),
                    "date": date_elem.text.strip() if date_elem else "",
                    "location": location_elem.text.strip() if location_elem else "",
                    "description": desc_elem.text.strip() if desc_elem else "",
                    "engagement": 0  # Default if not found
                }
                events.append(event)
            except Exception as e:
                logger.error(f"Error parsing aideadlines item: {e}")
                continue
        return events

    async def get_upcoming_events(self):
        # Get events from both sources
        html_events = self._get_events_from_html_link()
        rss_events = self._get_events_from_rss_feed()

        # Combine and deduplicate events
        temp_dict = {event["title"]: event for event in html_events + rss_events}
        temp_list = list(temp_dict.values())

        # Create Event objects
        new_events = [
            Event(
                title=event["title"],
                date=event["date"],
                location=event["location"],
                description=event["description"]
            ) for event in temp_list[:self.top_n]
        ]

        self.events.extend(new_events)
        return self.events