from typing import List, Optional
from pydantic import BaseModel

class NewsItem(BaseModel):
    title: str
    description: str
    link: str
    read_time: int
    source: Optional[str] = None
    engagement: Optional[str] = None
    additional_info: Optional[dict] = None

class Event(BaseModel):
    title: str
    date: str
    location: str
    description: str
    engagement: Optional[str] = None

class ResearchPaper(BaseModel):
    title: str
    authors: List[str]
    abstract: str
    publication: str
    impact: str
    link: str
    date: str
    engagement: Optional[str] = None

class NewsletterContent(BaseModel):
    highlights: List[dict]
    breaking_news: List[NewsItem]
    research_papers: List[ResearchPaper]
    latest_launch: List[NewsItem]
    github_trending: List[NewsItem]
    upcoming_events: List[Event]