import pytz
import logging
import feedparser
import numpy as np
import concurrent.futures
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, List
from db_handler import NewsItem
from email.utils import parsedate_to_datetime
from sklearn.feature_extraction.text import TfidfVectorizer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NewsService:
    def __init__(self, rss_urls: List[str]):
        self.rss_urls = rss_urls
        self.tfidf = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.summary = []
        self.news = []

    def _clean_html(self, text: str) -> str:
        if not text:
            return ''
        soup = BeautifulSoup(text, 'html.parser')
        return soup.get_text().strip()

    def _parse_date(self, date_str: str) -> datetime:
        try:
            parsed_date = parsedate_to_datetime(date_str)
            return parsed_date.replace(tzinfo=pytz.UTC)
        except:
            return datetime.min.replace(tzinfo=pytz.UTC)

    def _fetch_feed(self, url: str) -> List[Dict]:
        try:
            feed = feedparser.parse(url)
            news_items = []

            for entry in feed.entries:
                description = entry.get('description', '')
                if not description and 'content' in entry:
                    description = entry.content[0].value

                additional_info = {
                    'published_date': self._parse_date(entry.get('published', '')),
                    'author': entry.get('author', None),
                    'categories': entry.get('tags', []),
                    'guid': entry.get('id', None)
                }

                item = {
                    'title': entry.get('title', ''),
                    'description': self._clean_html(description),
                    'link': entry.get('link', ''),
                    'source': feed.feed.get('title', 'Unknown Source'),
                    'engagement': None,  # Can be updated if engagement metrics are available
                    'additional_info': additional_info,
                    'full_text': f"{entry.get('title', '')} {self._clean_html(description)}"  # for ranking
                }

                news_items.append(item)

            return news_items
        except Exception as e:
            print(f"Error fetching feed {url}: {str(e)}")
            return []

    def _calculate_importance_scores(self, news_items: List[Dict]) -> List[float]:
        if not news_items:
            return []
        try:
            texts = [item['full_text'] for item in news_items]
            x = self.tfidf.fit_transform(texts)
            doc_lengths = x.sum(axis=1).A1
            term_importance = np.sqrt(np.asarray(x.mean(axis=0)).ravel())
            scores = doc_lengths * np.dot(x.toarray(), term_importance)
            if len(scores) > 0:
                scores = (scores - scores.min()) / (scores.max() - scores.min() + 1e-8)
            return scores.tolist()
        except Exception as e:
            logger.error(f"Error calculating importance scores: {str(e)}")
            raise RuntimeError(f"Failed to calculate importance scores: {str(e)}")

    def _calculate_read_time(self, text: str, words_per_minute: int = 200) -> int:
        words = len(text.strip().split())
        total_minutes = words / words_per_minute
        minutes = int(total_minutes)
        seconds = int((total_minutes - minutes) * 60)
        return minutes

    async def get_highlights(self, max_items: int = 5) -> List[NewsItem]:
        today = datetime.now(pytz.UTC)
        all_news = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_url = {
                executor.submit(self._fetch_feed, url): url
                for url in self.rss_urls
            }

            for future in concurrent.futures.as_completed(future_to_url):
                news_items = future.result()
                all_news.extend(news_items)

        today_news = [
            item for item in all_news
            if item['additional_info']['published_date'].date() == today.date()
        ]

        if not today_news:
            return []

        importance_scores = self._calculate_importance_scores(today_news)

        for item, score in zip(today_news, importance_scores):
            item['additional_info']['importance_score'] = float(score)

        if len(today_news) > 1:
            sorted_news = sorted(
                today_news,
                key=lambda x: (
                    x['additional_info']['importance_score'],
                    x['additional_info']['published_date']
                ),
                reverse=True
            )
        else:
            sorted_news = today_news

        for item in sorted_news[:max_items]:
            read_time = self._calculate_read_time(item['description'])
            self.news.append(NewsItem(
                title=item['title'],
                description=item['description'],
                link=item['link'],
                read_time=read_time,
                source=item['source'],
                engagement=item['engagement'],
                additional_info=item['additional_info']
            ))
            self.summary.append({"title": item['title'], "read_time": read_time})
        return self.summary

    async def get_news(self):
        return self.news
