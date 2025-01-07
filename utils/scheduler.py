import asyncio
from builder.builder import NewsletterBuilder


async def daily_task():
    daily = NewsletterBuilder({
        "gh_url": "https://github.com/trending/python?since=weekly&spoken_language_code=en",
        "gh_ftype": "daily"})
    daily.set_sections(["news"])
    content = await daily.section_generator()
    newsletter_html = await daily.build(content)

    # Save the generated newsletter
    with open("static/daily_newsletter.html", "w") as f:
        f.write(newsletter_html)


async def weekly_task():
    weekly = NewsletterBuilder({
        "gh_url": "https://github.com/trending/python?since=weekly&spoken_language_code=en",
        "gh_ftype": "weekly"})
    weekly.set_sections(["all"])
    content = await weekly.section_generator()
    newsletter_html = await weekly.build(content)

    # Save the generated newsletter
    with open("static/weekly_newsletter.html", "w") as f:
        f.write(newsletter_html)



