import os
import os.path
import random
import logging
import sqlite3
import itertools
from threading import RLock
from collections import namedtuple

create_table = '''
    create table if not exists documents (
        code int primary key,
        is_present bool,
        is_old bool,
        error varchar
    )
    '''

Row = namedtuple('Row', ('code', 'is_present', 'is_old', 'error'))

def _wrap_put(f):
    def wrapped(self, code, *args):
        self._pre_put(code)
        f(self, code, *args)
        self._post_put(code)
    return wrapped

class LocalDocumentStore(object):

    def __init__(self, db, document_dir, code_range):
        os.makedirs(os.path.dirname(db), exist_ok=True)
        self.conn = sqlite3.connect(db)
        self.conn.execute(create_table)

        self.document_dir = document_dir
        os.makedirs(self.document_dir, exist_ok=True)

        self.pending = set()
        self.code_range = code_range

        self.logger = logging.getLogger(__name__).getChild(repr(self))

        self.lock = RLock()

    def __enter__(self):
        return self

    def __exit__(self):
        with self.lock:
            self.close()

    def close(self):
        with self.lock:
            self.conn.close()

    def next_code(self):
        with self.lock:
            while True:
                code = random.randint(*self.code_range) # not practical
                if code not in self.pending and self._get_row(code) is None:
                    self.pending.add(code)
                    return code

    def get(self, code):
        with self.lock:
            r = self._get_row(code)
            if r is not None and r.is_present:
                with open(self.get_document_path(code)) as f:
                    return f.read()

    @_wrap_put
    def put(self, code, document, is_old):
        with self.lock:
            if document is None:
                is_present = False
            else:
                is_present = True
                path = self.get_document_path(code)
                part_path = path + '.part'
                with open(part_path, 'w') as f:
                    f.write(document)
                os.rename(part_path, path) # rename is atomic
            self._put_row(Row(code, is_present, is_old, None))

    @_wrap_put
    def put_error(self, code, reason):
        with self.lock:
            self._put_row(Row(code, None, None, reason))

    def get_all_rows(self):
        with self.lock:
            cur = self.conn.cursor()
            it = cur.execute('select * from documents')
            return itertools.starmap(Row, it)

    def get_document_path(self, code):
        with self.lock:
            return os.path.join(self.document_dir, '{}.html'.format(code))

    def _get_row(self, code):
        with self.lock:
            cur = self.conn.cursor()
            it = cur.execute('select * from documents where code = ?', (code,))
            try:
                return Row(*next(it))
            except StopIteration:
                return None

    def _put_row(self, row):
        with self.lock:
            q = 'insert or replace into documents ({}) values ({})'.format(','.join(Row._fields), ','.join('?' for _ in Row._fields))
            cur = self.conn.cursor()
            cur.execute(q, tuple(row))
            self.conn.commit()

    def _pre_put(self, code):
        with self.lock:
            if self._get_row(code) is not None:
                self.logger.warning('already exists: %s', code)

    def _post_put(self, code):
        with self.lock:
            if code in self.pending:
                self.pending.remove(code)
