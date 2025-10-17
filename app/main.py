import time
import logging
import schedule
import configparser
import pandas as pd
import asyncio
from pathlib import Path
from utils import utility
from typing import Optional, List
from services import EmailService
from threading import Thread, Event
from db_handler import sites, Dynamo, TaskType
from builder.builder import NewsletterBuilder
from functools import wraps
from config.settings import get_config, setup_logging
from utils.cache import cache_result
from utils.metrics import metrics, track_time
from services.concurrent_email import ConcurrentEmailService
from db_handler.connection_pool import DynamoPool

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

stop_event = Event()
scheduler_thread: Optional[Thread] = None

class NewsletterScheduler:
    def __init__(self):
        self.config = get_config()
        setup_logging(self.config.log_level)
        self.is_running = False
        self.is_paused = False
        self.task_type: Optional[str] = None
        self.dynamo: Optional[Dynamo] = None
        self.dynamo_pool: Optional[DynamoPool] = None
        self.subscribers: List[str] = []
        self.email_service = ConcurrentEmailService(self.config.max_email_concurrent)
        self._initialize()
    
    def _initialize(self):
        try:
            config = configparser.ConfigParser()
            config_path = Path('db_handler/sample_vault/secrets.ini')
            if not config_path.exists():
                raise FileNotFoundError(f"Config file not found: {config_path}")
            
            config.read(config_path)
            region = config["Dynamo"]["region"]
            self.dynamo = Dynamo(region)
            self.dynamo_pool = DynamoPool(region, self.config.db_pool_size)
            
            csv_path = Path("db_handler/sample_vault/recipients.csv")
            if not csv_path.exists():
                raise FileNotFoundError(f"Recipients file not found: {csv_path}")
            
            df = pd.read_csv(csv_path)
            self.subscribers = df['email'].tolist()
            logger.info(f"Loaded {len(self.subscribers)} subscribers")
            
        except Exception as e:
            logger.error(f"Failed to initialize scheduler: {e}")
            raise

def retry(max_attempts: int = 3, delay: float = 1.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                    time.sleep(delay * (2 ** attempt))  # Exponential backoff
            return None
        return wrapper
    return decorator

scheduler = NewsletterScheduler()

def run_scheduler(task_type: str):
    def sync_wrapper(async_func):
        def wrapper():
            try:
                asyncio.run(async_func())
            except Exception as e:
                logger.error(f"Task execution failed: {e}")
        return wrapper
    
    if task_type == TaskType.WEEKLY.value:
        schedule.every().monday.at("00:00").do(sync_wrapper(weekly_task))
        logging.info("Weekly scheduler started")
    else:
        schedule.every().day.at("00:00").do(sync_wrapper(daily_task))
        logging.info("Daily scheduler started")

    scheduler.task_type = task_type
    scheduler.is_running = True
    
    while not stop_event.is_set():
        if not scheduler.is_paused:
            schedule.run_pending()
        time.sleep(1)

    schedule.clear()
    scheduler.is_running = False
    logging.info("Scheduler stopped")


@track_time('newsletter_generation')
@cache_result(ttl=1800)  # Cache for 30 minutes
async def generate_newsletter(sections: List[str], task_type: str, topics: Optional[List[str]] = None) -> str:
    # Input validation
    if not sections:
        raise ValueError("Sections list cannot be empty")
    
    valid_sections = ['news', 'research', 'github', 'competitions', 'products', 'events', 'all']
    invalid_sections = [s for s in sections if s not in valid_sections]
    if invalid_sections:
        raise ValueError(f"Invalid sections: {invalid_sections}. Valid sections: {valid_sections}")
    
    if task_type not in [TaskType.WEEKLY.value, TaskType.DAILY.value]:
        raise ValueError(f"Invalid task_type: {task_type}. Must be 'daily' or 'weekly'")
    
    try:
        if task_type == TaskType.WEEKLY.value:
            urls = sites["gh_weekly_url"]
        else:
            urls = sites["gh_daily_url"]

        builder = NewsletterBuilder({
            "gh_url": urls,
            "gh_ftype": task_type},
            scheduler.dynamo)
        builder.set_sections(sections)
        
        # Set custom topics if provided
        if topics:
            builder.set_topics(topics)
            logger.info(f"Custom topics set: {topics}")
        
        logger.info(f"Starting {task_type} newsletter generation")
        content = await builder.section_generator()
        logger.info("Sections generated")
        
        newsletter_html = await builder.build(content)
        newsletter_html = utility.inline_css(newsletter_html, "static")
        newsletter_html = utility.inline_svg_images(newsletter_html, "static")
        logger.info("Newsletter content processed")
        
        return newsletter_html
    except Exception as e:
        logger.error(f"Newsletter generation failed: {e}")
        raise


@track_time('newsletter_generation_markdown')
async def generate_newsletter_markdown(sections: List[str], task_type: str, topics: Optional[List[str]] = None) -> str:
    try:
        if task_type == TaskType.WEEKLY.value:
            urls = sites["gh_weekly_url"]
        else:
            urls = sites["gh_daily_url"]

        builder = NewsletterBuilder({
            "gh_url": urls,
            "gh_ftype": task_type},
            scheduler.dynamo)
        builder.set_sections(sections)
        
        if topics:
            builder.set_topics(topics)
            logger.info(f"Custom topics set for markdown: {topics}")
        
        logger.info(f"Starting {task_type} newsletter markdown generation")
        content = await builder.section_generator()
        logger.info("Sections generated for markdown")
        
        newsletter_md = await builder.build_markdown(content)
        logger.info("Newsletter markdown content processed")
        
        return newsletter_md
    except Exception as e:
        logger.error(f"Newsletter markdown generation failed: {e}")
        raise


async def daily_task():
    task_start_time = time.time()
    try:
        logger.info("Starting daily newsletter task")
        newsletter_html = await generate_newsletter(["news"], "daily")
        
        item = save_to_db(newsletter_html, "daily")
        logger.info(f"Newsletter saved to database with ID: {item['newsletterId']}")
        
        email_result = await send_email(content=item["content"])
        
        task_duration = time.time() - task_start_time
        logger.info(f"Daily newsletter task completed successfully in {task_duration:.2f}s")
        logger.info(f"Email status: {email_result.get('status', 'unknown')}")
        
    except Exception as e:
        task_duration = time.time() - task_start_time
        logger.error(f"Daily task failed after {task_duration:.2f}s: {e}")
        # Don't re-raise to prevent scheduler from stopping
        return False
    return True


async def weekly_task():
    task_start_time = time.time()
    try:
        logger.info("Starting weekly newsletter task")
        newsletter_html = await generate_newsletter(["all"], "weekly")
        
        item = save_to_db(newsletter_html, "weekly")
        logger.info(f"Newsletter saved to database with ID: {item['newsletterId']}")
        
        email_result = await send_email(content=item["content"])
        
        task_duration = time.time() - task_start_time
        logger.info(f"Weekly newsletter task completed successfully in {task_duration:.2f}s")
        logger.info(f"Email status: {email_result.get('status', 'unknown')}")
        
    except Exception as e:
        task_duration = time.time() - task_start_time
        logger.error(f"Weekly task failed after {task_duration:.2f}s: {e}")
        # Don't re-raise to prevent scheduler from stopping
        return False
    return True


def save_to_db(content: str, content_type: str) -> dict:
    try:
        item = {
            "item_name": "newsletter",
            "type": content_type,
            "content": content,
            "created": utility.get_formatted_timestamp()
        }

        item_id = utility.generate_deterministic_id(item, key_fields=["item_name", "type"], prefix="nl")
        item["newsletterId"] = item_id
        
        if scheduler.dynamo is None:
            raise RuntimeError("Database connection not initialized")
        
        scheduler.dynamo.add_item("newsletter", "newsletterId", item, False)
        logger.info(f"Newsletter saved to database with ID: {item_id}")
        return item
    except Exception as e:
        logger.error(f"Error saving to dynamo db: {e}")
        raise


@retry(max_attempts=3, delay=2.0)
def _send_email_with_retry(email_service: EmailService) -> dict:
    return email_service.send_email()

@track_time('email_sending')
async def send_email(content: Optional[str] = None, template_id: Optional[str] = None, recipients: Optional[List[str]] = None) -> dict:
    try:
        if recipients is None:
            recipients = scheduler.subscribers
        
        if not recipients:
            logger.warning("No recipients provided for email sending")
            return {"status": "error", "message": "No recipients"}
        
        # Use concurrent email service for better performance
        result = await scheduler.email_service.send_emails_concurrent(
            recipients=recipients,
            content=content or "",
            subject="Newsletter"
        )
        
        # Update metrics
        metrics.set_gauge('active_subscribers', len(recipients))
        metrics.increment_counter('emails_sent', result.get('successful', 0))
        
        logger.info(f"Email batch completed: {result.get('successful', 0)}/{len(recipients)} successful")
        return result
    except Exception as e:
        logger.error(f"Email sending failed: {e}")
        metrics.increment_counter('email_errors')
        raise

def health_check() -> dict:
    """Check system health status"""
    checks = {
        'scheduler_initialized': scheduler.dynamo is not None,
        'subscribers_loaded': len(scheduler.subscribers) > 0,
        'scheduler_running': scheduler.is_running,
        'config_files_exist': (
            Path('db_handler/sample_vault/secrets.ini').exists() and
            Path('db_handler/sample_vault/recipients.csv').exists()
        )
    }
    
    status = 'healthy' if all(checks.values()) else 'unhealthy'
    
    return {
        'status': status,
        'checks': checks,
        'subscriber_count': len(scheduler.subscribers),
        'task_type': scheduler.task_type,
        'timestamp': utility.get_formatted_timestamp(),
        'metrics': metrics.get_metrics()
    }

def graceful_shutdown():
    """Gracefully shutdown the scheduler"""
    logger.info("Initiating graceful shutdown...")
    stop_event.set()
    
    if scheduler_thread and scheduler_thread.is_alive():
        logger.info("Waiting for scheduler thread to finish...")
        scheduler_thread.join(timeout=30)
        
        if scheduler_thread.is_alive():
            logger.warning("Scheduler thread did not finish within timeout")
        else:
            logger.info("Scheduler thread finished successfully")
    
    schedule.clear()
    scheduler.is_running = False
    logger.info("Graceful shutdown completed")
