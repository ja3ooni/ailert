from services.news_service import NewsService
from services.event_service import EventsService
from services.research_service import ResearchService
from services.apps.gh_service import GitHubScanner
from services.competition_service import CompetitionService
from services.product_service import ProductService
from services.email_service import EmailService


__all__ = [
    "NewsService",
    "GitHubScanner",
    "CompetitionService",
    "EventsService",
    "ResearchService",
    "ProductService",
    "EmailService"
]