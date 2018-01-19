##
# this module provides code to store the inverted index into disk
# and load it from memory
##

from database.sqlite_handler import AbstractSQLiteHandler


class ZonedSQLiteHandler(AbstractSQLiteHandler):

    def create_index_tables(self):
        """
        creates two tables called Token and Posting
        and creates an index on Token table
        """

        self.cursor.executescript("""
            CREATE TABLE IF NOT EXISTS Token (token_id INT PRIMARY KEY, token TEXT);

            CREATE TABLE IF NOT EXISTS Posting (token_id INT, doc_id INT, zone TEXT, positional_index INT,
                PRIMARY KEY (token_id, doc_id, zone, positional_index), FOREIGN KEY (token_id) REFERENCES Token(token_id));

            CREATE UNIQUE INDEX IF NOT EXISTS token_index ON Token(token);
        """)


    def insert_index_entry(self, term_id, term, postings_list):
        """
        stores inverted index on disk
        :param term_id:
        :param term:
        :param postings_list:
        """

        self.cursor.execute("INSERT INTO Token VALUES (?, ?)", (term_id, term))

        postings_tuples = []
        for doc_id in postings_list:
            for zone in postings_list[doc_id]:
                for pos in postings_list[doc_id][zone]['pos']:
                    postings_tuples += [(term_id, doc_id, zone, pos)]

        self.cursor.executemany("INSERT INTO Posting VALUES (?, ?, ?, ?)", postings_tuples)


    def load_index(self):
        """
        loads the inverted index from disk into memory
        :return:
        """

        self.cursor.execute("SELECT token_id, token FROM Token")
        token_rows = self.cursor.fetchall()

        token_dictionary = {}
        for row in token_rows:
            token_id = int(row[0])
            token = row[1]

            token_dictionary[token_id] = token

        self.cursor.execute("SELECT token_id, doc_id, zone, positional_index FROM Posting")
        posting_rows = self.cursor.fetchall()

        inverted_index = {}
        for row in posting_rows:
            token_id = int(row[0])
            doc_id = int(row[1])
            zone = row[2]
            positional_index = int(row[3])

            term = token_dictionary[token_id]

            if term in inverted_index:
                # if the document exists already in the postings list then update
                # the term frequency and the positional index
                if doc_id in inverted_index[term]['postings']:
                    if zone in inverted_index[term]['postings'][doc_id]:
                        inverted_index[term]['postings'][doc_id][zone]['pos'] += [positional_index]
                    else:
                        inverted_index[term]['postings'][doc_id][zone] = {'pos': [positional_index]}
                # if the document does not exist in the postings list, add it to the postings list
                else:
                    inverted_index[term]['postings'][doc_id] = {zone: {'pos': [positional_index]}}
            # if the term does not exist in the inverted index
            else:
                inverted_index[term] = {'postings': {doc_id: {zone: {'pos': [positional_index]}}}}

        return inverted_index
