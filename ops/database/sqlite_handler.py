##
# this module provides code to store the inverted index into disk
# and load it from memory
##

import sqlite3

def open_connection(db_file):
    conn = sqlite3.connect(db_file)
    conn.execute('PRAGMA synchronous=OFF')
    conn.execute('PRAGMA foreign_keys=ON')
    return conn, conn.cursor()


def close_connection(conn):
    conn.close()

'''
creates two tables called Token and Posting
and creates an index on Token table
'''
def create_index_tables(cursor):
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS Token (token_id INT PRIMARY KEY, token TEXT, df INT);

        CREATE TABLE IF NOT EXISTS Posting (token_id INT, doc_id INT, positional_index INT,
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
def insert_index_entry(cursor, term_id, term, postings_list, df):
    cursor.execute("INSERT INTO Token VALUES (?, ?, ?)", (term_id, term, df))

    postings_tuples = []
    for doc_id in postings_list:
        for pos in postings_list[doc_id]['pos']:
            postings_tuples += [(term_id, doc_id, pos)]

    cursor.executemany("INSERT INTO Posting VALUES (?, ?, ?)", postings_tuples)

'''
loads postings list from disk
'''
def load_postings_list(db_file, term):
    conn, cursor = open_connection(db_file)
    cursor.execute("SELECT DISTINCT p.doc_id FROM Token t INNER JOIN Posting p on p.token_id = t.token_id WHERE t.token = :term", {"term": term})
    postings_list = cursor.fetchall()
    close_connection(conn)

    return [r[0] for r in postings_list]

'''
loads positional index from disk
'''
def load_positional_index(db_file, terms):
    conn, cursor = open_connection(db_file)
    # token ids are loaded by term texts and because terms is a list, IN operator is used in the query and to make the
    # query parameterized, ? has been put for each term
    cursor.execute("SELECT token_id, token, df FROM Token WHERE token IN (%s)" % (",".join(["?"] * len(terms))), tuple(terms))
    rows = cursor.fetchall()

    inverted_index = {}

    for row in rows:
        token_id = int(row[0])
        token = row[1]
        df = int(row[2])

        cursor.execute(
            "SELECT token_id, doc_id, positional_index FROM Posting WHERE token_id = :token_id",
            {"token_id": token_id})
        posting_rows = cursor.fetchall()

        for pr in posting_rows:
            doc_id = int(pr[1])
            positional_index = int(pr[2])

            if token in inverted_index:
                if doc_id in inverted_index[token]['postings']:
                    inverted_index[token]['postings'][doc_id]['pos'] += [positional_index]
                    inverted_index[token]['postings'][doc_id]['tf'] += 1
                else:
                    inverted_index[token]['postings'][doc_id] = {'pos': [positional_index], 'tf': 1}
            else:
                inverted_index[token] = {'postings': {doc_id: {'pos': [positional_index], 'tf': 1}}, 'df': df}

    close_connection(conn)

    return inverted_index

'''
loads the inverted index from disk into memory
'''
def load_index(db_file):
    conn, cursor = open_connection(db_file)

    cursor.execute("SELECT token_id, token, df FROM Token")
    token_rows = cursor.fetchall()

    token_dictionary = {}
    for row in token_rows:
        token_id = int(row[0])
        token = row[1]
        df = int(row[2])
        token_dictionary[token_id] = (token, df)

    cursor.execute("SELECT token_id, doc_id, positional_index FROM Posting")
    posting_rows = cursor.fetchall()

    close_connection(conn)

    inverted_index = {}
    for row in posting_rows:
        token_id = int(row[0])
        doc_id = int(row[1])
        positional_index = int(row[2])

        token = token_dictionary[token_id]

        if token[0] in inverted_index:
            if doc_id in inverted_index[token[0]]['postings']:
                inverted_index[token[0]]['postings'][doc_id]['pos'] += [positional_index]
                inverted_index[token[0]]['postings'][doc_id]['tf'] += 1
            else:
                inverted_index[token[0]]['postings'][doc_id] = {'pos': [positional_index], 'tf': 1}
        else:
            inverted_index[token[0]] = {'postings': {doc_id: {'pos': [positional_index], 'tf': 1}}, 'df': token[1]}

    return inverted_index


def commit(conn):
    conn.commit()


def rollback(conn):
    conn.rollback()


