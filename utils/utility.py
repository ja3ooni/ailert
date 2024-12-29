from dbhandler.db import *

FEATURES_FILE = os.path.join(DATA_DIR, 'features.p')

def save_features(features):
    safe_pickle_dump(features, FEATURES_FILE)

def load_features():
    """ loads the features dict from disk """
    with open(FEATURES_FILE, 'rb') as f:
        features = pickle.load(f)
    return features

def get_tags():
    if g.user is None:
        return {}
    if not hasattr(g, '_tags'):
        with get_tags_db() as tags_db:
            tags_dict = tags_db[g.user] if g.user in tags_db else {}
        g._tags = tags_dict
    return g._tags

def get_papers():
    if not hasattr(g, '_pdb'):
        g._pdb = get_papers_db()
    return g._pdb

def get_metas():
    if not hasattr(g, '_mdb'):
        g._mdb = get_metas_db()
    return g._mdb