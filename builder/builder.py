import re
import logging
import asyncio
from typing import Dict, Any
from services import *
from typing import List
from db_handler import rss_feed
from datetime import datetime
from utils.utility import load_template, truncate_text
from db_handler import NewsItem, Competitions, ResearchPaper, Products, Repo, Event, NewsletterContent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NewsletterBuilder:
    def __init__(self, dict_vars: Dict, db_object: Any, brand_name: str = "AiLert", template_path: str = "static/newsletter.html", sections=None):
        self.sections = sections if sections else ["all"]
        self.brand_name = brand_name
        self.template_path = template_path
        self.db_object = db_object
        self.template = load_template(self.template_path)
        self.news_service = NewsService(rss_feed)
        self.research_service = ResearchService()
        self.github_service = GitHubScanner(dict_vars["gh_url"], dict_vars["gh_ftype"])
        self.product_service = ProductService()
        self.competition_service = CompetitionService()
        self.events_service = EventsService()

    def set_sections(self, sections):
        self.sections = sections

    def _format_highlights(self, highlights: List[dict]) -> str:
        """Format highlights section with proper list items"""
        formatted_items = []
        total_time = 0

        for h in highlights:
            read_time = h.get('read_time', 0)
            total_time += read_time
            formatted_items.append(f'<li>{h["title"]} ({read_time} min read)</li>')

        return (
            '<div class="section summary-section">'
            f'<h2 class="section-title">📋 This Week\'s Highlights</h2>'
            '<div class="read-time">'
            '<i class="far fa-clock"></i>'
            f'<span>Total reading time: {total_time} minutes</span>'
            '</div>'
            '<ul>'
            f'{chr(10).join(formatted_items)}'
            '</ul>'
            '</div>'
        )

    def _format_news_items(self, items: List[NewsItem]) -> str:
        formatted = []
        for item in items:
            engagement_html = (
                f'<div class="trending-button"><i class="fas fa-fire"></i>'
                f'<span>{item.engagement} readers engaged</span></div>'
            ) if item.engagement else ''

            formatted.append(
                '<div class="news-item">'
                f'<div class="news-title"><a href="{item.link}" target="_blank">{item.title}</a></div>'
                f'<p>{truncate_text(item.description, 300)}...</p>'
                f'{engagement_html}'
                '</div>'
            )
        return chr(10).join(formatted)

    def _format_research(self, papers: List[ResearchPaper]) -> str:
        formatted = []
        for paper in papers:
            engagement_html = (
                f'<div class="trending-button"><i class="fas fa-fire"></i>'
                f'<span>{paper.engagement} researchers interested</span></div>'
            ) if paper.engagement else ''

            formatted.append(
                '<div class="news-item">'
                f'<div class="news-title"><a href="{paper.link}" target="_blank">{paper.title}</a></div>'
                f'<p>Authors: {", ".join(paper.authors)}</p>'
                f'<p>{truncate_text(paper.abstract, 250)}...</p>'
                f'<p>Published in: {paper.publication}</p>'
                f'{engagement_html}'
                '</div>'
            )
        return chr(10).join(formatted)

    def _format_competitions(self, competitions: List[Competitions]) -> str:
        formatted = []
        for comp in competitions:
            formatted.append(
                '<div class="news-item">'
                f'<div class="news-title"><a href="{comp.link}" target="_blank">{comp.name}</a></div>'
                f'<p>Deadline: {comp.deadline}</p>'
                f'<p>Reward: <b>${comp.reward}</b></p>'
                '</div>'
            )
        return chr(10).join(formatted)

    def _format_products(self, products: List[Products]) -> str:
        formatted = []
        for product in products:
            engagement_html = (
                f'<div class="trending-button"><i class="fas fa-fire"></i>'
                f'<span>{product.engagement} tech enthusiasts watching</span></div>'
            ) if product.engagement else ''

            formatted.append(
                '<div class="news-item">'
                f'<div class="news-title"><a href="{product.link}" target="_blank">{product.name}</a></div>'
                f'<p>{truncate_text(product.summary, 200)}...</p>'
                f'{engagement_html}'
                '</div>'
            )
        return chr(10).join(formatted)

    def _format_repos(self, repos: List[Repo]) -> str:
        formatted = []
        for repo in repos:
            engagement_html = (
                f'<div class="trending-button"><i class="fas fa-fire"></i>'
                f'<span>{repo.engagement} stars</span></div>'
            ) if repo.engagement else ''

            formatted.append(
                '<div class="news-item">'
                f'<div class="news-title"><a href="https://github.com/{repo.name}" target="_blank">{repo.name}</a></div>'
                f'<p>{truncate_text(repo.summary, 200)}...</p>'
                f'{engagement_html}'
                '</div>'
            )
        return chr(10).join(formatted)

    def _format_events(self, events: List[Event]) -> str:
        formatted = []
        for event in events:
            formatted.append(
                '<div class="news-item">'
                f'<div class="news-title">{event.title}</div>'
                f'<p>Date: {event.date}</p>'
                f'<p>Location: {event.location}</p>'
                f'<p>{truncate_text(event.description, 200)}...</p>'
                '</div>'
            )
        return chr(10).join(formatted)

    async def section_generator(self, selected_sections: List[str] = None) -> NewsletterContent:
        if not selected_sections:
            selected_sections = ["all"]

        content = {
            "highlights": None,
            "breaking_news": None,
            "research_papers": None,
            "latest_competitions": None,
            "top_products": None,
            "github_trending": None,
            "upcoming_events": None
        }

        try:
            if "all" in selected_sections:
                logger.info("Generating all sections")
                tasks = [
                    asyncio.create_task(self.news_service.get_highlights(3), name="highlights"),
                    asyncio.create_task(self.news_service.get_news(), name="news"),
                    asyncio.create_task(self.research_service.get_latest_papers(), name="papers"),
                    asyncio.create_task(self.competition_service.get_latest_competitions(), name="competitions"),
                    asyncio.create_task(self.product_service.get_latest_products(), name="products"),
                    asyncio.create_task(self.github_service.get_trending_repos(), name="github"),
                    asyncio.create_task(self.events_service.get_upcoming_events(), name="events")
                ]
                completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)

                for task, result in zip(tasks, completed_tasks):
                    if isinstance(result, Exception):
                        logger.error(f"Error in {task.get_name()}: {str(result)}")
                    else:
                        logger.info(f"Successfully completed {task.get_name()}")
                        content_key = {
                            "highlights": "highlights",
                            "news": "breaking_news",
                            "papers": "research_papers",
                            "competitions": "latest_competitions",
                            "products": "top_products",
                            "github": "github_trending",
                            "events": "upcoming_events"
                        }[task.get_name()]
                        content[content_key] = result
            else:
                tasks = []
                if "news" in selected_sections:
                    logger.info("Generating news sections")
                    tasks.extend([
                        asyncio.create_task(self.news_service.get_highlights(10), name="highlights"),
                        asyncio.create_task(self.news_service.get_news(), name="news")
                    ])
                if "papers" in selected_sections:
                    logger.info("Generating research section")
                    tasks.append(asyncio.create_task(self.research_service.get_latest_papers(), name="papers"))
                if "latest" in selected_sections:
                    logger.info("Generating latest products and competitions")
                    tasks.extend([
                        asyncio.create_task(self.competition_service.get_latest_competitions(), name="competitions"),
                        asyncio.create_task(self.product_service.get_latest_products(), name="products")
                    ])
                if "trending" in selected_sections:
                    logger.info("Generating GitHub trends")
                    tasks.append(asyncio.create_task(self.github_service.get_trending_repos(), name="github"))
                if "upcoming" in selected_sections:
                    logger.info("Generating upcoming events")
                    tasks.append(asyncio.create_task(self.events_service.get_upcoming_events(), name="events"))

                completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
                for task, result in zip(tasks, completed_tasks):
                    if isinstance(result, Exception):
                        logger.error(f"Error in {task.get_name()}: {str(result)}")
                    else:
                        logger.info(f"Successfully completed {task.get_name()}")
                        content_key = {
                            "highlights": "highlights",
                            "news": "breaking_news",
                            "papers": "research_papers",
                            "competitions": "latest_competitions",
                            "products": "top_products",
                            "github": "github_trending",
                            "events": "upcoming_events"
                        }[task.get_name()]
                        content[content_key] = result

        except Exception as e:
            logger.error(f"Error generating sections: {str(e)}")
            raise

        return NewsletterContent(**content)

    def _format_share_section(self) -> str:
        return '''
        <div class="section share-section">
            <h2 class="section-title">❤️ Love AiLert?</h2>
            <p>Help fellow AI enthusiasts stay ahead of the curve!</p>
            <a href="#" class="share-button"><i class="fas fa-envelope"></i> Share via Email</a>
            <a href="#" class="share-button"><i class="fab fa-twitter"></i> Share on X</a>
            <a href="#" class="share-button"><i class="fab fa-linkedin"></i> Share on LinkedIn</a>
        </div>'''

    def _format_feedback_section(self) -> str:
        return '''
        <div class="section feedback-section">
            <h2 class="section-title">💝 Enjoying AiLert?</h2>
            <p>Your feedback shapes our future editions!</p>
            <div class="feedback-buttons">
                <button class="feedback-button positive">
                    <i class="fas fa-thumbs-up"></i> Loving It!
                </button>
                <button class="feedback-button negative">
                    <i class="fas fa-thumbs-down"></i> Could Be Better
                </button>
            </div>
        </div>'''

    async def build(self, content: NewsletterContent) -> str:
        logger.info("Starting newsletter build")
        sections = []

        # Add highlights section
        if content.highlights:
            logger.info("Adding highlights section")
            sections.append(self._format_highlights(content.highlights))

        section_count = 0
        section_map = [
            ("🌐 Latest Industry News", content.breaking_news, self._format_news_items),
            ("📚 Research Spotlight", content.research_papers, self._format_research),
            ("🏆 Latest Competitions", content.latest_competitions, self._format_competitions),
            ("🚀 New Products", content.top_products, self._format_products),
            ("💻 GitHub Trending", content.github_trending, self._format_repos),
            ("📅 Upcoming Events", content.upcoming_events, self._format_events)
        ]

        for title, items, formatter in section_map:
            if items:
                logger.info(f"Adding section: {title}")
                formatted_content = formatter(items)
                sections.append(
                    '<div class="section">'
                    f'<h2 class="section-title">{title}</h2>'
                    f'{formatted_content}'
                    '</div>'
                )
                section_count += 1
                if section_count == 2:
                    logger.info("Adding share section")
                    sections.append(self._format_share_section())

        logger.info("Adding feedback section")
        sections.append(self._format_feedback_section())

        # Combine all sections
        combined_content = chr(10).join(sections)

        # Replace template variables
        newsletter_content = self.template
        newsletter_content = newsletter_content.replace('{{content}}', combined_content)
        newsletter_content = newsletter_content.replace('{{brand_name}}', self.brand_name)
        newsletter_content = newsletter_content.replace('{{current_year}}', str(datetime.now().year))

        # Clean up any remaining template variables
        newsletter_content = re.sub(r'{{.*?}}', '', newsletter_content)
        newsletter_content = re.sub(r'\{\{#each.*?}}', '', newsletter_content)
        newsletter_content = re.sub(r'\{\{/each}}', '', newsletter_content)

        return newsletter_content