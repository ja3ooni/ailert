from news_service import NewsService
from event_service import EventsService
from research_service import ResearchService
from services.apps.gh_service import GitHubScanner
from competition_service import CompetitionService


__all__ = [
    "NewsService",
    "GitHubScanner",
    "CompetitionService",
    "EventsService",
    "ResearchService"
]