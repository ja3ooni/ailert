import time
import schedule
from utils.scheduler import *
from flask import Blueprint

bp = Blueprint("ailert", __name__, url_prefix="/internal/v1")


@bp.get("/init-weekly-scheduler")
async def start_weekly_scheduler():
    schedule.every().monday.at("00:00").do(weekly_task)
    print("Scheduler is running. Waiting for the weekly task...")
    while True:
        schedule.run_pending()
        time.sleep(1)


@bp.get("/init-daily-scheduler")
async def start_daily_scheduler():
    schedule.every().day.at("00:00").do(daily_task)
    print("Scheduler is running. Waiting for the daily task...")
    while True:
        schedule.run_pending()
        time.sleep(1)