import os
import sqlite3, zlib, pickle, tempfile
from sqlitedict import SqliteDict
from contextlib import contextmanager

DATA_DIR = 'data'

@contextmanager
def _tempfile(*args, **kws):
    fd, name = tempfile.mkstemp(*args, **kws)
    os.close(fd)
    try:
        yield name
    finally:
        try:
            os.remove(name)
        except OSError as e:
            if e.errno == 2:
                pass
            else:
                raise e


@contextmanager
def open_atomic(filepath, *args, **kwargs):
    fsync = kwargs.pop('fsync', False)

    with _tempfile(dir=os.path.dirname(filepath)) as tmppath:
        with open(tmppath, *args, **kwargs) as f:
            yield f
            if fsync:
                f.flush()
                os.fsync(f.fileno())
        os.rename(tmppath, filepath)

def safe_pickle_dump(obj, fname):
    with open_atomic(fname, 'wb') as f:
        pickle.dump(obj, f, -1) # -1 specifies highest binary protocol


class CompressedSqliteDict(SqliteDict):
    def __init__(self, *args, **kwargs):

        def encode(obj):
            return sqlite3.Binary(zlib.compress(pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)))

        def decode(obj):
            return pickle.loads(zlib.decompress(bytes(obj)))

        super().__init__(*args, **kwargs, encode=encode, decode=decode)

PAPERS_DB_FILE = os.path.join(DATA_DIR, 'papers.db')
DICT_DB_FILE = os.path.join(DATA_DIR, 'dict.db')

def get_papers_db(flag='r', autocommit=True):
    assert flag in ['r', 'c']
    pdb = CompressedSqliteDict(PAPERS_DB_FILE, tablename='papers', flag=flag, autocommit=autocommit)
    return pdb

def get_metas_db(flag='r', autocommit=True):
    assert flag in ['r', 'c']
    mdb = SqliteDict(PAPERS_DB_FILE, tablename='metas', flag=flag, autocommit=autocommit)
    return mdb

def get_tags_db(flag='r', autocommit=True):
    assert flag in ['r', 'c']
    tdb = CompressedSqliteDict(DICT_DB_FILE, tablename='tags', flag=flag, autocommit=autocommit)
    return tdb

def get_last_active_db(flag='r', autocommit=True):
    assert flag in ['r', 'c']
    ladb = SqliteDict(DICT_DB_FILE, tablename='last_active', flag=flag, autocommit=autocommit)
    return ladb

def get_email_db(flag='r', autocommit=True):
    assert flag in ['r', 'c']
    edb = SqliteDict(DICT_DB_FILE, tablename='email', flag=flag, autocommit=autocommit)
    return edb


FEATURES_FILE = os.path.join(DATA_DIR, 'features.p')

def save_features(features):
    """ takes the features dict and save it to disk in a simple pickle file """
    safe_pickle_dump(features, FEATURES_FILE)

def load_features():
    """ loads the features dict from disk """
    with open(FEATURES_FILE, 'rb') as f:
        features = pickle.load(f)
    return features
