import numpy as np
import configparser
from sklearn import svm
from dbhandler import sites
from typing import List, Dict

from dbhandler import ResearchPaper
from services.apps import ArxivScanner
from services.apps import OpenReviewScanner
from sklearn.feature_extraction.text import TfidfVectorizer


config = configparser.ConfigParser()
config.read('dbhandler/vault/secrets.ini')

class ResearchService:
    def __init__(self, top_n:int = 3):
        self.top_n = top_n
        self. arxiv = ArxivScanner(sites["arxiv_url"], top_n=top_n)
        self.open_review = OpenReviewScanner(top_n=top_n)
        self.top_papers = []

    def _rerank(self, apapers: List[Dict], opapers: List[Dict]) -> List[Dict]:
        all_papers = apapers
        texts = [f"{p['title']} {p['abstract']} {' '.join(p['authors'])}" for p in all_papers]

        vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        x = vectorizer.fit_transform(texts)
        y = np.zeros(len(all_papers))
        for i, paper in enumerate(all_papers):
            score = float(paper.get('score', 0))
            citations = float(paper.get('citations', 0))
            y[i] = score + 0.1 * citations

        if y.max() > y.min():
            y = (y - y.min()) / (y.max() - y.min())

        clf = svm.LinearSVC(
            class_weight='balanced',
            max_iter=1000,
            dual=False
        )
        clf.fit(x, y > np.median(y))
        scores = clf.decision_function(x)
        scored_papers = [(paper, score) for paper, score in zip(all_papers, scores)]
        reranked = sorted(scored_papers, key=lambda x: x[1], reverse=True)
        return [paper for paper, _ in reranked[:self.top_n]]

    async def get_latest_papers(self):
        search_query = config["Arxiv"]["q"]
        arxiv_papers = self.arxiv.get_top_n_papers(search_query=search_query)
        open_r_papers = self.open_review.get_top_n_papers()
        reranked_papers = self._rerank(arxiv_papers, open_r_papers)
        self.top_papers.extend(ResearchPaper(
            title = paper["title"],
            abstract= paper["abstract"],
            authors = paper["authors"],
            publication = paper["publication"],
            date = paper["_time_str"],
            link = paper["url"],
            engagement = "") for paper in reranked_papers)
        return self.top_papers
