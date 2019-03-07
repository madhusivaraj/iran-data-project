import os
import os.path
import sqlite3
import itertools
from base64 import b64decode
from binascii import hexlify
from collections import namedtuple
from threading import RLock

# c:        Base64-decoded c paramter
# solution: Solution as string. last guessed if incorrect
# state:    One of STATE_*. If state == STATE_INCORRECT, the image content
#           should be found in <self.image_dir>/<hex-encoded c>.jpg
# agent:    One of AGENT_*, for debugging.
create_table = '''
    create table if not exists captchas (
        c char(16) primary key,
        solution varchar,
        state int,
        agent int
    )
    '''

STATE_CORRECT = 0
STATE_INCORRECT = 1
STATE_UNKNOWN = 2

AGENT_HUMAN = 0
AGENT_COMPUTER = 1

Row = namedtuple('Row', 'c solution state agent')

class LocalCaptchaCache(object):

    def __init__(self, db, image_dir):
        os.makedirs(os.path.dirname(db), exist_ok=True)
        self.conn = sqlite3.connect(db)
        self.conn.execute(create_table)
        self.image_dir = image_dir
        os.makedirs(self.image_dir, exist_ok=True)

    def __enter__(self):
        return self

    def __exit__(self):
        self.close()

    def get(self, c):
        r = self.get_row(c)
        if r is None or r.state == STATE_INCORRECT:
            return None
        else:
            return r.solution

    def report_correct(self, c, solution):
        r = self.get_row(c)
        if r is None:
            r = Row(c, solution, STATE_CORRECT, AGENT_COMPUTER)
        else:
            if self.exists_image(c):
                os.remove(self.get_image_path(c))
            r = r._replace(state=STATE_CORRECT)
        self.put_row(r)

    def report_incorrect(self, c, solution, content):
        r = self.get_row(c)
        if r is None:
            r = Row(c, solution, STATE_INCORRECT, AGENT_COMPUTER)
        else:
            r = r._replace(state=STATE_CORRECT)
        # Replace old incorrect solution and image with new, out of laziness.
        self.put_row(r)
        with open(self.get_image_path(c), 'wb') as f:
            f.write(content)

    def report_unexpected_incorrect(self, c):
        r = self.get_row(c)
        if r is None:
            raise Exception('user error')
        if r.state == STATE_INCORRECT:
            raise Exception('user error')
        self.put_row(r._replace(state=STATE_INCORRECT))

    def close(self):
        self.conn.close()

    def get_row(self, c):
        cur = self.conn.cursor()
        it = cur.execute('select * from captchas where c = ?', (c,))
        try:
            return Row(*next(it))
        except StopIteration:
            return None

    def get_all_rows(self):
        cur = self.conn.cursor()
        it = cur.execute('select * from captchas')
        return itertools.starmap(Row, it)

    def put_row(self, row):
        q = 'insert or replace into captchas ({}) values ({})'.format(','.join(Row._fields), ','.join('?' for _ in Row._fields))
        cur = self.conn.cursor()
        cur.execute(q, tuple(row))
        self.conn.commit()

    def get_image_path(self, c):
        return os.path.join(self.image_dir, '{}.jpg'.format(hexlify(c).decode('ascii')))

    def exists_image(self, c):
        return os.path.isfile(self.get_image_path(c))
