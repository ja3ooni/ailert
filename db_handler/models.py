from enum import Enum
from pydantic import BaseModel
from typing import List, Optional

class TaskType(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"

class SchedulerState(Enum):
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"

class NewsItem(BaseModel):
    title: str
    description: str
    link: str
    read_time: int
    source: Optional[str] = None
    engagement: Optional[str] = None
    additional_info: Optional[dict] = None

class Competitions(BaseModel):
    name: str
    link: str
    deadline: str
    reward: str

class Repo(BaseModel):
    name: str
    link: str
    summary: str
    source: Optional[str] = None
    engagement: Optional[str] = None

class Products(BaseModel):
    name: str
    link: str
    summary: str
    source: Optional[str] = None
    engagement: Optional[str] = None

class Event(BaseModel):
    title: str
    date: str
    location: str
    description: str

class ResearchPaper(BaseModel):
    title: str
    authors: List[str]
    abstract: str
    publication: str
    link: str
    date: str
    engagement: Optional[str] = None

class NewsletterContent(BaseModel):
    # model_config = dict(arbitrary_types_allowed=True)
    highlights: List[dict] | None = None
    breaking_news: List[NewsItem] | None = None
    research_papers: List[ResearchPaper] | None = None
    latest_competitions: List[Competitions] | None = None
    top_products: List[Products] | None = None
    github_trending: List[Repo] | None = None
    upcoming_events: List[Event] | None = None