import os
import time
import random
import logging
import sqlite3
import pickle
import zlib
import urllib.request
import feedparser
import numpy as np
from sklearn import svm
from typing import List, Dict, Any, Optional, Tuple
from sqlitedict import SqliteDict


class ArxivScanner:
    def __init__(self, base_rul: str, top_n: int = 5, data_dir: str = 'data'):
        self.base_url = base_rul
        self.top_n = top_n
        self.data_dir = data_dir
        self.logger = logging.getLogger(__name__)
        os.makedirs(data_dir, exist_ok=True)

        self.papers_db_file = os.path.join(data_dir, 'papers.db')
        self.features_file = os.path.join(data_dir, 'features.p')
        self.default_query = 'cat:cs.CV+OR+cat:cs.LG+OR+cat:cs.CL+OR+cat:cs.AI+OR+cat:cs.NE+OR+cat:cs.RO'

    def _get_compressed_db(self, tablename: str, flag: str = 'r') -> SqliteDict:
        return SqliteDict(
            self.papers_db_file,
            tablename=tablename,
            flag=flag,
            encode=lambda obj: sqlite3.Binary(zlib.compress(pickle.dumps(obj, -1))),
            decode=lambda obj: pickle.loads(zlib.decompress(bytes(obj)))
        )

    def _load_features(self) -> Any:
        if os.path.exists(self.features_file):
            with open(self.features_file, 'rb') as f:
                return pickle.load(f)
        return None

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

            paper.pop('summary_detail', None)
            paper.pop('title_detail', None)

            papers.append(paper)

        return papers

    def rank_papers(self, papers: List[Dict], method: str = 'time',
                    query: str = None, similar_to_pid: str = None,
                    tags: List[str] = None) -> List[Tuple[Dict, float]]:
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

        elif method == 'similar' and (similar_to_pid or tags):
            features = self._load_features()
            if not features:
                self.logger.error("No features file found for similarity ranking")
                return [(p, 0.0) for p in papers]

            x, pids = features['x'], features['pids']
            n, d = x.shape

            pid_to_idx = {pid: i for i, pid in enumerate(pids)}

            y = np.zeros(n, dtype=np.float32)
            if similar_to_pid and similar_to_pid in pid_to_idx:
                y[pid_to_idx[similar_to_pid]] = 1.0
            elif tags:
                for paper in papers:
                    if any(tag in paper.get('tags', []) for tag in tags):
                        if paper['_id'] in pid_to_idx:
                            y[pid_to_idx[paper['_id']]] = 1.0

            if y.sum() == 0:
                return [(p, 0.0) for p in papers]

            clf = svm.LinearSVC(class_weight='balanced', verbose=False, max_iter=10000, tol=1e-6, C=0.01)
            clf.fit(x, y)
            scores = clf.decision_function(x)

            scored_papers = []
            for p in papers:
                if p['_id'] in pid_to_idx:
                    score = scores[pid_to_idx[p['_id']]]
                    scored_papers.append((p, float(score)))
                else:
                    scored_papers.append((p, 0.0))

        else:
            # Default to time-based ranking
            scored_papers = [(p, -p['_time']) for p in papers]

        return sorted(scored_papers, key=lambda x: x[1], reverse=True)

    def get_top_n_papers(self, search_query: Optional[str] = None,
                         rank_method: str = 'time', similar_to_pid: str = None,
                         tags: List[str] = None, store_results: bool = True) -> List[Dict[str, Any]]:
        query = search_query or self.default_query
        papers = []
        start_index = 0

        while len(papers) < self.top_n:
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

        ranked_papers = self.rank_papers(
            papers,
            method=rank_method,
            query=search_query,
            similar_to_pid=similar_to_pid,
            tags=tags
        )

        if store_results:
            with self._get_compressed_db('papers', 'c') as db:
                for paper, _ in ranked_papers[:self.top_n]:
                    db[paper['_id']] = paper

        return [{
            'id': p['_id'],
            'title': p['title'],
            'authors': [a['name'] for a in p['authors']],
            'abstract': p['summary'],
            'categories': [t['term'] for t in p['tags']],
            'published': p['_time_str'],
            'url': f"https://arxiv.org/abs/{p['_id']}",
            'pdf_url': f"https://arxiv.org/pdf/{p['_id']}.pdf",
            'score': score,
            'publication': "ARXIV"
        } for p, score in ranked_papers[:self.top_n]]

    def get_paper(self, paper_id: str) -> Optional[Dict[str, Any]]:
        with self._get_compressed_db('papers', 'r') as db:
            paper = db.get(paper_id)
            if paper:
                return {
                    'id': paper['_id'],
                    'title': paper['title'],
                    'authors': [a['name'] for a in paper['authors']],
                    'abstract': paper['summary'],
                    'categories': [t['term'] for t in paper['tags']],
                    'published': paper['_time_str'],
                    'url': f"https://arxiv.org/abs/{paper['_id']}",
                    'pdf_url': f"https://arxiv.org/pdf/{paper['_id']}.pdf"
                }
        return None