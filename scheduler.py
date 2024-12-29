from builder.builder import NewsletterBuilder


def daily_task():
    daily = NewsletterBuilder("template/newsletter.html")
    daily.set_sections(["news"])
    content = daily.section_generator()
    newsletter_html = daily.build(content)

    # Save the generated newsletter
    with open("template/dail_newsletter.html", "w") as f:
        f.write(newsletter_html)


def weekly_task():
    weekly = NewsletterBuilder("template/newsletter.html")
    weekly.set_sections(["all"])
    content = weekly.section_generator()
    newsletter_html = weekly.build(content)

    # Save the generated newsletter
    with open("template/dail_newsletter.html", "w") as f:
        f.write(newsletter_html)



