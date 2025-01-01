from services.apps import KaggleScanner


class CompetitionService:
    def __init__(self):
        self.kaggle = KaggleScanner

    def get_latest_launch(self):
        pass