import time
import numpy as np
from sklearn import svm
from random import shuffle
import urllib.request as libreq
from utils.utility import *

class ArxivScanner:
    def __init__(self, url, top_n=5, sort="desc"):
        self.url = url
        self.top_n = top_n
        self.sort = sort
        self.response = []

    def __random_rank(self):
        mdb = get_metas()
        pids = list(mdb.keys())
        shuffle(pids)
        scores = [0 for _ in pids]
        return pids, scores

    def __time_rank(self):
        mdb = get_metas()
        ms = sorted(mdb.items(), key=lambda kv: kv[1]['_time'], reverse=True)
        tnow = time.time()
        pids = [k for k, v in ms]
        scores = [(tnow - v['_time']) / 60 / 60 / 24 for k, v in ms]  # time delta in days
        return pids, scores

    def __svm_rank(self, tags: str = '', pid: str = '', C: float = 0.01):
        if not (tags or pid):
            return [], [], []

        features = load_features()
        x, pids = features['x'], features['pids']
        n, d = x.shape
        ptoi, itop = {}, {}
        for i, p in enumerate(pids):
            ptoi[p] = i
            itop[i] = p

        y = np.zeros(n, dtype=np.float32)
        if pid:
            y[ptoi[pid]] = 1.0
        elif tags:
            tags_db = get_tags()
            tags_filter_to = tags_db.keys() if tags == 'all' else set(tags.split(','))
            for tag, pids in tags_db.items():
                if tag in tags_filter_to:
                    for pid in pids:
                        y[ptoi[pid]] = 1.0

        if y.sum() == 0:
            return [], [], []

        # classify
        clf = svm.LinearSVC(class_weight='balanced', verbose=False, max_iter=10000, tol=1e-6, C=C)
        clf.fit(x, y)
        s = clf.decision_function(x)
        sortix = np.argsort(-s)
        pids = [itop[ix] for ix in sortix]
        scores = [100 * float(s[ix]) for ix in sortix]

        # get the words that score most positively and most negatively for the svm
        ivocab = {v: k for k, v in features['vocab'].items()}  # index to word mapping
        weights = clf.coef_[0]  # (n_features,) weights of the trained svm
        sortix = np.argsort(-weights)
        words = []
        for ix in list(sortix[:40]) + list(sortix[-20:]):
            words.append({
                'word': ivocab[ix],
                'weight': weights[ix],
            })
        return pids, scores, words

    def __search_rank(self, q: str = ''):
        if not q:
            return [], []  # no query? no results
        qs = q.lower().strip().split()  # split query by spaces and lowercase

        pdb = get_papers()
        match = lambda s: sum(min(3, s.lower().count(qp)) for qp in qs)
        matchu = lambda s: sum(int(s.lower().count(qp) > 0) for qp in qs)
        pairs = []
        for pid, p in pdb.items():
            score = 0.0
            score += 10.0 * matchu(' '.join([a['name'] for a in p['authors']]))
            score += 20.0 * matchu(p['title'])
            score += 1.0 * match(p['summary'])
            if score > 0:
                pairs.append((score, pid))

        pairs.sort(reverse=True)
        pids = [p[1] for p in pairs]
        scores = [p[0] for p in pairs]
        return pids, scores

    def __search_papers(self):
        with libreq.urlopen(self.url) as url:
            r = url.read()
        print(r)




