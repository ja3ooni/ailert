from dbhandler import Competitions
from services.apps import KaggleScanner

class CompetitionService:
    def __init__(self):
        self.kaggle = KaggleScanner()
        self.competitions = []

    async def get_latest_competitions(self):
        kaggle = self.kaggle.get_new_competitions_launch()
        self.competitions.extend([Competitions(
            name = comp["name"],
            link = comp["link"],
            deadline = comp["deadline"],
            reward = comp["reward"]
        ) for comp in kaggle])

        return self.competitions