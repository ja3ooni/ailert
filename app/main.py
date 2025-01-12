import time
import logging
import schedule
import configparser
import pandas as pd
from utils import utility
from typing import Optional
from services import EmailService
from threading import Thread, Event
from db_handler import sites, Dynamo, TaskType
from builder.builder import NewsletterBuilder

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

stop_event = Event()
scheduler_thread: Optional[Thread] = None
scheduler_state = {"is_running": False, "is_paused": False, "task_type": None}

config = configparser.ConfigParser()
config.read('db_handler/vault/secrets.ini')
region = config["Dynamo"]["region"]

dynamo = Dynamo(region)

df = pd.read_csv("db_handler/vault/recipients.csv")
subscribers = df['email'].tolist()

def run_scheduler(task_type: str):
    if task_type == TaskType.WEEKLY.value:
        schedule.every().monday.at("00:00").do(weekly_task)
        logging.info("Weekly scheduler started")
    else:
        schedule.every().day.at("00:00").do(daily_task)
        logging.info("Daily scheduler started")

    while not stop_event.is_set():
        if not scheduler_state["is_paused"]:
            schedule.run_pending()
        time.sleep(1)

    schedule.clear()
    scheduler_state["is_running"] = False
    logging.info("Scheduler stopped")


async def generate_newsletter(sections, task_type):
    if task_type == TaskType.WEEKLY.value:
        urls = sites["gh_weekly_url"]
    else:
        urls = sites["gh_daily_url"]

    weekly = NewsletterBuilder({
        "gh_url": urls,
        "gh_ftype": task_type},
        dynamo)
    weekly.set_sections(sections)
    content = await weekly.section_generator()
    newsletter_html = await weekly.build(content)
    return newsletter_html


async def daily_task():
    daily = NewsletterBuilder({
        "gh_url": sites["gh_daily_url"],
        "gh_ftype": "daily"},
        dynamo)
    daily.set_sections(["news"])
    logger.info(f"starting generator")
    content = await daily.section_generator()
    logger.info(f"sections generated")
    newsletter_html = await daily.build(content)
    newsletter_html = utility.inline_css(newsletter_html, "static")
    newsletter_html = utility.inline_svg_images(newsletter_html, "static")
    logger.info("content updated")
    item = save_to_db(newsletter_html, "daily")
    logger.info(f"saved to db, sending email")
    await send_email(content=item["content"])
    logger.info(f"email sent")


async def weekly_task():
    weekly = NewsletterBuilder({
        "gh_url": sites["gh_weekly_url"],
        "gh_ftype": "weekly"},
        dynamo)
    weekly.set_sections(["all"])
    logger.info(f"starting generator")
    content = await weekly.section_generator()
    logger.info(f"sections generated")
    newsletter_html = await weekly.build(content)
    logger.info(f"newsletter build complete")
    newsletter_html = utility.inline_css(newsletter_html, "static")
    newsletter_html = utility.inline_svg_images(newsletter_html, "static")
    logger.info("content updated")
    item = save_to_db(newsletter_html, "weekly")
    logger.info(f"saved to db, sending email")
    await send_email(content=item["content"])
    logger.info(f"email sent")


def save_to_db(content, content_type):
    try:
        item = {
            "item_name": "newsletter",
            "type": content_type,
            "content": content,
            "created": utility.get_formatted_timestamp()
        }

        item_id = utility.generate_deterministic_id(item, key_fields=["item_name", "type"], prefix="nl")
        item["newsletterId"] = item_id
        dynamo.add_item("newsletter", "newsletterId", item, False)
        return item
    except Exception as e:
        logging.info("Error saving to dynamo db", e)


async def send_email(content=None, template_id=None, recipients=subscribers):
    email_service = EmailService(
        recipients=recipients,
        body_text = content,
        template_id=template_id
    )
    result = email_service.send_email()
    return result
