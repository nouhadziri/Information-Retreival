##
# this module provides code to store the inverted index into disk
# and load it from memory
##

from database.sqlite_handler import AbstractSQLiteHandler


class LabeledSQLiteHandler(AbstractSQLiteHandler):

    def create_index_tables(self):
        """
        creates tables :Token, Posting, Document
        and creates an index on Token table
        """

        self.cursor.executescript("""
            CREATE TABLE IF NOT EXISTS Token (token_id INT PRIMARY KEY, token TEXT, df INT);

            CREATE TABLE IF NOT EXISTS Posting (token_id INT, doc_id INT, tf INT,
                PRIMARY KEY (token_id, doc_id), FOREIGN KEY (token_id) REFERENCES Token(token_id));

            CREATE TABLE IF NOT EXISTS Document (doc_id INT PRIMARY KEY, class TEXT, doc_len REAL);

            CREATE UNIQUE INDEX IF NOT EXISTS token_index ON Token(token);
        """)

    def insert_index_entry(self, term_id, term, postings_list, df):
        """
        stores inverted index on disk
        :param term_id:
        :param term:
        :param postings_list:
        """

        self.cursor.execute("INSERT INTO Token VALUES (?, ?, ?)", (term_id, term, df))

        postings_tuples = [(term_id, doc_id, postings_list[doc_id]['tf']) for doc_id in postings_list]
        self.cursor.executemany("INSERT INTO Posting VALUES (?, ?, ?)", postings_tuples)

    def insert_doc_entry(self, doc_id, clazz, doc_len):
        self.cursor.execute("INSERT INTO Document VALUES (?, ?, ?)", (doc_id, clazz, doc_len))

    def load_index(self):
        """
        loads the inverted index from disk into memory
        :return:
        """

        self.cursor.execute("SELECT token_id, token, df FROM Token")
        token_rows = self.cursor.fetchall()

        token_dictionary = {}
        for i, row in enumerate(token_rows):
            token_id = int(row[0])
            token = row[1]
            df = int(row[2])

            token_dictionary[token_id] = (token, df, i)

        self.cursor.execute("SELECT token_id, doc_id, tf FROM Posting")
        posting_rows = self.cursor.fetchall()

        inverted_index = {}
        for row in posting_rows:
            token_id = int(row[0])
            doc_id = int(row[1])
            tf = int(row[2])

            token_tuple = token_dictionary[token_id]
            term = token_tuple[0]

            if term in inverted_index:
                inverted_index[term]['postings'][doc_id] = {'tf': tf}
            # if the term does not exist in the inverted index
            else:
                inverted_index[term] = {'postings': {doc_id: {'tf': tf}}, 'df': token_tuple[1], 'i': token_tuple[2]}

        return inverted_index

    def load_doc_index(self):
        self.cursor.execute("SELECT doc_id, class, doc_len FROM Document")
        docs = self.cursor.fetchall()

        doc_dictionary = {}
        for row in docs:
            doc_id = int(row[0])
            clazz = row[1]
            doc_len = float(row[2])

            doc_dictionary[doc_id] = {'class': clazz, 'length': doc_len}

        return doc_dictionary