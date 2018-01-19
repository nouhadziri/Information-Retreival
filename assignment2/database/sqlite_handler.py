##
# this module provides code to store the inverted index into disk
# and load it from memory
##

from abc import ABCMeta

import sqlite3


class AbstractSQLiteHandler(object):
    __metaclass__ =  ABCMeta

    def __init__(self, db_file):
        self.db_file = db_file
        self.connection = None
        self.cursor = None
        self.__nullify()
        self.open_connection()

    def __nullify(self):
        self.connection = None
        self.cursor = None

    def is_open(self):
        return self.connection is not None

    def open_connection(self):
        self.connection = sqlite3.connect(self.db_file)
        self.connection.execute('PRAGMA synchronous=OFF')
        self.connection.execute('PRAGMA foreign_keys=ON')
        self.cursor = self.connection.cursor()

    def close_connection(self):
        if self.is_open():
            self.connection.close()
            self.__nullify()

    def commit(self):
        if self.is_open():
            self.connection.commit()
        else:
            raise RuntimeError('commit invoked on a closed connection')

    def rollback(self):
        if self.is_open():
            self.connection.rollback()
        else:
            raise RuntimeError('rollback invoked on a closed connection')




'''
creates two tables :Token and Posting
and creates an index on Token table
'''
def create_index_tables(cursor):
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS Token (token_id INT PRIMARY KEY, token TEXT);

        CREATE TABLE IF NOT EXISTS Posting (token_id INT, doc_id INT, zone TEXT, positional_index INT,
            PRIMARY KEY (token_id, doc_id, positional_index), FOREIGN KEY (token_id) REFERENCES Token(token_id));

        CREATE UNIQUE INDEX IF NOT EXISTS token_index ON Token(token);
    """)

'''
creates a table called DocumentLength to store the 'length'
of all documents in the collection
'''
def create_document_length_table(cursor):
    cursor.execute("CREATE TABLE IF NOT EXISTS DocumentLength (doc_id INT PRIMARY KEY, doc_len REAL)")


def insert_document_length(cursor, doc_id, length ):
    cursor.execute("INSERT INTO DocumentLength VALUES (?,?) ", (doc_id,length))


def is_document_length_exists(cursor):
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name = ?", ('DocumentLength',))
    return cursor.fetchone()[0] > 0


def get_number_of_documents(cursor):
    cursor.execute("SELECT COUNT(DISTINCT doc_id) FROM Posting")
    return cursor.fetchone()[0]


def load_document_length(cursor):
    cursor.execute("SELECT doc_id, doc_len FROM DocumentLength")
    rows = cursor.fetchall()
    return dict((int(r[0]), int(r[1])) for r in rows)


'''
stores inverted index on disk
'''
def insert_index_entry(cursor, term_id, term, postings_list):
    cursor.execute("INSERT INTO Token VALUES (?, ?)", (term_id, term))

    postings_tuples = []
    for doc_id in postings_list:
        for zone in postings_list[doc_id]:
            for pos in postings_list[doc_id][zone]['pos']:
                postings_tuples += [(term_id, doc_id, zone,pos)]

    cursor.executemany("INSERT INTO Posting VALUES (?, ?, ?, ?)", postings_tuples)


