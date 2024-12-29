import configparser
from services import *
from services.crawler import *
from dbhandler.models import *
from datetime import datetime
from services.apps.arx_service import ArxivScanner

config = configparser.ConfigParser()
config.read('vault/vault.ini')


class NewsletterBuilder:
    def __init__(self, template_path: str, brand_name: str = "AiLert", sections=None):
        self.sections = sections if sections else ["all"]
        self.template_path = template_path
        self.brand_name = brand_name
        self.template = self._load_template()
        self.reader = RSSReader()
        self.arxiv_obj = ArxivScanner()
        self.gh_obj = GitHubScanner()
        self.hf_obj = HuggingFaceScanner()
        self.ph_obj = ProductHuntScanner()
        self.kg_obj = KaggleScanner()
        self.events_obj = EventsCrawler()
        self.substack_obj = SubstackCrawler()
        self.linkedin_obj = LinkedinCrawler()
        self.twitter_obj = TwitterCrawler()

    def set_sections(self, sections):
        if sections:
            self.sections = sections

    def _load_template(self) -> str:
        with open(self.template_path, 'r') as f:
            return f.read()

    def _format_highlights_section(self, highlights: List[dict]) -> str:
        if not highlights:
            return ""

        total_time = sum(item.get('read_time', 0) for item in highlights)
        highlights_html = "\n".join([
            f'<li>{item["title"]} ({item["read_time"]} min read)</li>'
            for item in highlights
        ])

        return f'''
        <div class="section summary-section">
            <h2 class="section-title">📋 This Week's Highlights</h2>
            <div class="read-time">
                <i class="far fa-clock"></i>
                <span>Total reading time: {total_time} minutes</span>
            </div>
            <p>In this power-packed edition:</p>
            <ul>
                {highlights_html}
            </ul>
        </div>
        '''

    def _format_news_item(self, item: NewsItem) -> str:
        engagement_html = ""
        if item.engagement:
            engagement_html = f'''
            <div class="trending-button">
                <i class="fas fa-fire"></i>
                <span>{item.engagement}</span>
            </div>
            '''

        return f'''
        <div class="news-item">
            <div class="news-title">{item.title}</div>
            <p>{item.description}</p>
            {engagement_html}
        </div>
        '''

    def _format_research_paper(self, paper: ResearchPaper) -> str:
        return f'''
        <div class="news-item">
            <div class="news-title">{paper.title}</div>
            <p>Authors: {', '.join(paper.authors)}<br>
            Published in: {paper.publication}<br>
            Impact: {paper.impact}</p>
            <div class="trending-button">
                <i class="fas fa-fire"></i>
                <span>{paper.engagement}</span>
            </div>
        </div>
        '''

    def _format_event(self, event: Event) -> str:
        return f'''
        <div class="news-item">
            <div class="news-title">{event.title}</div>
            <p>Date: {event.date}<br>
            Location: {event.location}<br>
            {event.description}</p>
            <div class="trending-button">
                <i class="fas fa-fire"></i>
                <span>{event.engagement}</span>
            </div>
        </div>
        '''

    def _get_section_content(self, section_title: str, content_items: List, formatter_method) -> str:
        if not content_items:
            return ""

        items_html = ''.join([formatter_method(item) for item in content_items])
        return f'''
        <div class="section">
            <h2 class="section-title">{section_title}</h2>
            {items_html}
        </div>
        '''

    def _get_share_section(self):
        share_section = '''
                        <div class="section share-section">
                            <h2 class="section-title" style="color: white; border-color: rgba(255,255,255,0.2);">❤️ Love AiLert?</h2>
                            <p>Help fellow AI enthusiasts stay ahead of the curve!</p>
                            <a href="#" class="share-button"><i class="fas fa-envelope"></i> Share via Email</a>
                            <a href="#" class="share-button"><i class="fab fa-twitter"></i> Share on X</a>
                            <a href="#" class="share-button"><i class="fab fa-linkedin"></i> Share on LinkedIn</a>
                        </div>
                        '''
        return share_section

    def section_generator(self):
        content = NewsletterContent(
            highlights=self.news_service.get_highlights(),
            breaking_news=self.news_service.get_breaking_news(),
            research_papers=self.research_service.get_latest_papers(),
            latest_launches=self.news_service.get_latest_launches(),
            github_trending=self.github_service.get_trending_repos(),
            upcoming_events=self.events_service.get_upcoming_events()
        )
        return content

    def build(self, content: NewsletterContent) -> str:
        newsletter = self.template

        container_start = newsletter.find('<div class="container">')
        container_end = newsletter.rfind('</div>') + 6
        header_end = newsletter.find('<div class="section summary-section">')
        if header_end == -1:
            header_end = newsletter.find('<div class="section">')
        header = newsletter[container_start:header_end]

        footer_start = newsletter.rfind('<div class="footer">')
        footer = newsletter[footer_start:container_end]

        sections = []
        if content.highlights:
            sections.append(self._format_highlights_section(content.highlights))

        section_configs = [
            ("🌐 Breaking Industry News", content.breaking_news, self._format_news_item),
            ("📚 Breakthrough Research", content.research_papers, self._format_research_paper),
            ("🚀 Latest AI Launches", content.latest_launches, self._format_news_item),
            ("💻 GitHub Trending This Week", content.github_trending, self._format_news_item),
            ("📅 Must-Attend AI Events", content.upcoming_events, self._format_event)
        ]

        for title, items, formatter in section_configs:
            if len(sections) == 2:
                sections.append(self._get_share_section)
            if items:
                sections.append(self._get_section_content(title, items, formatter))

        feedback_section = '''
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
                </div>
                '''
        sections.append(feedback_section)

        newsletter_content = header + '\n'.join(sections) + footer

        # Update metadata
        newsletter_content = newsletter_content.replace('{{BRAND_NAME}}', self.brand_name)
        newsletter_content = newsletter_content.replace('{{CURRENT_YEAR}}', str(datetime.now().year))

        # Rebuild the full HTML document
        doc_start = newsletter[:container_start]
        doc_end = newsletter[container_end:]

        return doc_start + newsletter_content + doc_end