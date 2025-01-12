# AiLert ![logo.svg](static/logo.svg)

An open-source AI newsletter platform that aggregates and curates AI content from across the internet.

## Overview
AiLert automatically aggregates content from 150+ sources including research papers, news sites, GitHub repositories, and events to create customizable AI newsletters. Built with Python and powered by AWS, it helps communities and teams stay updated with the latest in AI.

## Features
- 📚 Multi-source aggregation (150+ sources)
- 🎯 Smart content categorization
- 📊 Engagement tracking
- ⚡ Async content processing
- 📧 Customizable newsletter templates
- 📅 Daily and weekly digest options

## Content Sources
- Research Papers (arXiv)
- Industry News (RSS feeds)
- GitHub Trending Repositories
- AI Competitions & Events
- Product Launches
- Technical Blogs

## Tech Stack
- Python 3.8+
- Flask
- AWS DynamoDB
- BeautifulSoup4
- Feedparser
- Schedule
- Pydantic
- uvicorn

## 📫 How to Subscribe

1. Visit https://ailert.tech
2. Navigate to the newsletter section
3. Enter your email address
4. Confirm your subscription

## ✨ What Our Readers Say

`"AIlert's newsletter helps me stay on top of AI developments without getting overwhelmed" - Tech Lead at Fortune 500`


`"The perfect blend of technical depth and practical insights" - AI Researcher`

## 🔒 Your Privacy Matters

- No spam, ever
- Unsubscribe anytime
- Your data is never shared or sold

## 📅 Publication Schedule
Receive our carefully curated insights every week, delivered straight to your inbox.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ailert.git
cd ailert
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up AWS credentials:
```bash
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"
export AWS_REGION="your_region"
```

4. Run the application:
```bash
python main.py
```

## Project Structure
```
ailert/
├── builder/            # Newsletter generation
├── db_handler/         # Db operations manager
├── app/                # Core functions of the application
├── router/             # REST Api routes
├── services/           # Content aggregation services
├── static/             # Templates and assets
├── utils/              # Application common utilities
├── main.py             # Flask application
└── requirements.txt    # Dependencies
```

## Contributing
We welcome contributions of all kinds! Here are some ways you can help:

### Development
- Add new content sources
- Improve content categorization
- Optimize performance
- Add new features
- Fix bugs
- Write tests

### Documentation
- Improve technical docs
- Write tutorials
- Add code comments
- Create examples

### Design
- Improve newsletter templates
- Create visual assets
- Enhance UI/UX

### Content
- Add new RSS feeds
- Improve content filtering
- Suggest new features

## Getting Started with Contributing

1. Fork the repository
2. Create a new branch
```bash
git checkout -b feature/your-feature
```
3. Make your changes
4. Write or update tests
5. Submit a pull request

### Development Setup
1. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

2. Run tests:
```bash
python -m pytest
```

## API Documentation

### Newsletter Builder
```python
from builder.builder import NewsletterBuilder

# Create daily newsletter
daily = NewsletterBuilder({
    "gh_url": "github_url",
    "gh_ftype": "daily"
})
daily.set_sections(["news"])
content = await daily.section_generator()
```

### Content Services
Each service handles different content types:
- `NewsService`: Industry news
- `ResearchService`: Research papers
- `GitHubScanner`: Trending repositories
- `ProductService`: New AI products
- `CompetitionService`: AI competitions
- `EventsService`: Upcoming events

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments
- All our amazing contributors
- The open-source community
- RSS feed providers
- Content creators

## Contact
- Create an issue for bug reports
- Start a discussion for feature requests
- Join our Discord community [link]

## Roadmap
- [ ] Add more content sources
- [ ] Implement ML-based content ranking
- [ ] Add personalization options
- [ ] Create API endpoints
- [ ] Add email delivery system
- [ ] Improve template customization

---
Built with ❤️ for the AI community