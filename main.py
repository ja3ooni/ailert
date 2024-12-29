import schedule
import time

from scheduler import *

if __name__ == "__main__":

    schedule.every().day.at("00:00").do(daily_task)
    schedule.every().monday.at("00:00").do(weekly_task)

    print("Scheduler is running. Waiting for the daily task...")

    while True:
        schedule.run_pending()
        time.sleep(1)