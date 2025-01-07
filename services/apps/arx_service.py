import time
import random
import logging
import urllib.request
import feedparser
import numpy as np
from sklearn import svm
from typing import List, Dict, Any, Optional, Tuple


class ArxivScanner:
    def __init__(self, base_url: str, top_n: int = 5):
        self.base_url = base_url
        self.top_n = top_n
        self.logger = logging.getLogger(__name__)
        self.default_query = 'cat:cs.CV+OR+cat:cs.LG+OR+cat:cs.CL+OR+cat:cs.AI+OR+cat:cs.NE+OR+cat:cs.RO'

    def _get_response(self, search_query: str, start_index: int = 0) -> bytes:
        query_url = f'{self.base_url}search_query={search_query}&sortBy=lastUpdatedDate&start={start_index}&max_results=100'

        with urllib.request.urlopen(query_url) as url:
            response = url.read()
            if url.status != 200:
                raise Exception(f"ArXiv API returned status {url.status}")
        return response

    def _parse_arxiv_url(self, url: str) -> tuple:
        idv = url[url.rfind('/') + 1:]
        parts = idv.split('v')
        return idv, parts[0], int(parts[1])

    def _parse_response(self, response: bytes) -> List[Dict[str, Any]]:
        def encode_feedparser_dict(d):
            if isinstance(d, feedparser.FeedParserDict) or isinstance(d, dict):
                return {k: encode_feedparser_dict(d[k]) for k in d.keys()}
            elif isinstance(d, list):
                return [encode_feedparser_dict(k) for k in d]
            return d

        papers = []
        parse = feedparser.parse(response)

        for entry in parse.entries:
            paper = encode_feedparser_dict(entry)
            idv, raw_id, version = self._parse_arxiv_url(paper['id'])

            paper['_idv'] = idv
            paper['_id'] = raw_id
            paper['_version'] = version
            paper['_time'] = time.mktime(paper['updated_parsed'])
            paper['_time_str'] = time.strftime('%b %d %Y', paper['updated_parsed'])

            papers.append(paper)

        return papers

    def rank_papers(self, papers: List[Dict], method: str = 'time',
                    query: str = None) -> List[Tuple[Dict, float]]:
        if not papers:
            return []

        if method == 'time':
            scored_papers = [(p, -p['_time']) for p in papers]

        elif method == 'random':
            scored_papers = [(p, random.random()) for p in papers]

        elif method == 'search' and query:
            query_terms = query.lower().strip().split()
            scored_papers = []

            for p in papers:
                score = 0.0
                score += 20.0 * sum(1 for term in query_terms if term in p['title'].lower())
                score += 10.0 * sum(
                    1 for term in query_terms if term in ' '.join(a['name'].lower() for a in p['authors']))
                score += 5.0 * sum(1 for term in query_terms if term in p['summary'].lower())
                scored_papers.append((p, score))

        elif method == 'svm':
            from sklearn.feature_extraction.text import TfidfVectorizer

            # Prepare text data
            texts = []
            times = []
            for p in papers:
                try:
                    title = p['title']
                    authors = ' '.join(a['name'] for a in p['authors'])
                    summary = p.get('summary', '')
                    texts.append(f"{title} {authors} {summary}")
                    times.append(-p['_time'])  # Negative time for more recent = higher score
                except Exception as e:
                    self.logger.error(f"Error processing paper: {e}")
                    continue

            if not texts:
                return [(p, 0.0) for p in papers]

            # Create TF-IDF features
            vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english'
            )
            X = vectorizer.fit_transform(texts)

            # Create binary labels based on median time
            median_time = np.median(times)
            y = np.array([1 if t > median_time else 0 for t in times])

            # Train SVM
            clf = svm.LinearSVC(
                class_weight='balanced',
                random_state=42,
                max_iter=10000
            )

            try:
                clf.fit(X, y)
                scores = clf.decision_function(X)
                scored_papers = []
                for paper, score in zip(papers, scores):
                    scored_papers.append((paper, float(score)))
            except Exception as e:
                self.logger.error(f"Error in SVM ranking: {e}")
                return [(p, -p['_time']) for p in papers]  # Fallback to time-based ranking

        else:
            scored_papers = [(p, -p['_time']) for p in papers]

        return sorted(scored_papers, key=lambda x: x[1], reverse=True)

    def get_top_n_papers(self, search_query: Optional[str] = None,
                         rank_method: str = 'svm') -> List[Dict[str, Any]]:
        query = search_query or self.default_query
        papers = []
        start_index = 0

        while len(papers) < max(100, self.top_n):  # Get more papers for better SVM training
            try:
                response = self._get_response(query, start_index)
                batch = self._parse_response(response)
                if not batch:
                    break
                papers.extend(batch)
                start_index += len(batch)
                time.sleep(1 + random.uniform(0, 3))
            except Exception as e:
                self.logger.error(f"Error fetching papers: {e}")
                break
        ranked_papers = self.rank_papers(papers, method=rank_method, query=search_query)

        return [{
            'id': p['_id'],
            'title': p['title'],
            'authors': [a['name'] for a in p['authors']],
            'abstract': p['summary'],
            'categories': [t['term'] for t in p['tags']],
            '_time_str': p['_time_str'],
            'url': f"https://arxiv.org/abs/{p['_id']}",
            'pdf_url': f"https://arxiv.org/pdf/{p['_id']}.pdf",
            'score': score,
            'publication': "ARXIV"
        } for p, score in ranked_papers[:self.top_n]]