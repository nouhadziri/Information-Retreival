import re
import math

from clusterer_sqlite_handler import ClustererSQLiteHandler
from util.errors import DirectoryNotFoundError
from util.fancy import *
import util.analyzer as analyzer
from collections import defaultdict
from os import listdir
from os.path import isfile, join, exists
from nltk.tokenize import word_tokenize
from sqlite3 import IntegrityError, OperationalError, DatabaseError


def create(document_dir):
    """
    creates an inverted index given an English text corpus
    for movies. If the directory provided does not exist,
    the program will print an error. If the filenames
    in the test corpus do not match with the description,
    the program will print an error and will skip the
    document.
    :param document_dir:
    :return:
    """
    if not exists(document_dir):
        raise DirectoryNotFoundError

    term_index = {}
    doc_index = {}
    for f in listdir(document_dir):
        file_path = join(document_dir, f)
        if isfile(file_path):

            matched_doc_id = re.search('\d+', f)
            if matched_doc_id is None:
                print '[WARNING] The file name does not match with the description: %s' % f
                continue

            matched_doc_id_group = matched_doc_id.group()
            doc_id = int(matched_doc_id_group)
            doc_index[doc_id] = {}

            with open(file_path, 'r') as doc:
                for line in doc:
                    create_index_per_line(doc_id, line, term_index)

    create_document_length_vector(doc_index, term_index)

    return term_index, doc_index


def create_document_length_vector(doc_index, term_index):
    # N = len(doc_index)
    doc_word_map = defaultdict(lambda: defaultdict(float))
    for term in term_index:

        # idf = math.log(1.0 * N / term_index[term]['df'])

        for doc in term_index[term]['postings']:
            doc_word_map[doc][term] = 1 + math.log(term_index[term]['postings'][doc]['tf'])
    for doc in doc_word_map:
        doc_index[doc]['length'] = math.sqrt(sum(doc_word_map[doc][term] ** 2 for term in doc_word_map[doc]))


def create_index_per_line(doc_id, line, term_index):
    words = word_tokenize(line.decode('utf-8'))  # tokenize the document using NLTK tokenizer
    for word in words:
        try:
            term = analyzer.normalize(word)  # applies stemming, drops stop words
            # converts to lower case and removes punctuation

            # if the term is already in the index then update its postings list
            if term in term_index:
                # if the document exists already in the postings list then update
                # the term frequency and the positional index
                if doc_id in term_index[term]['postings']:
                    term_index[term]['postings'][doc_id]['tf'] += 1
                # if the document does not exist in the postings list, add it to the postings list
                else:
                    term_index[term]['postings'][doc_id] = {'tf': 1}
                    term_index[term]['df'] += 1
            # if the term does not exist in the inverted index
            else:
                term_index[term] = {'postings': {doc_id: {'tf': 1}}, 'df': 1}
        except Warning:
            continue


def save(inverted_index, doc_index, output_file):
    """
    saves the inverted index in a sqlite database
    :param inverted_index:
    :param doc_index:
    :param output_file:
    :return:
    """
    if inverted_index is None:
        return

    sqlite_handler = ClustererSQLiteHandler(output_file)
    sqlite_handler.create_index_tables()

    try:
        term_id = 1
        for term in inverted_index:
            sqlite_handler.insert_index_entry(term_id, term, inverted_index[term]['postings'], inverted_index[term]['df'])
            term_id += 1

            if term_id % 1000 == 0:
                sqlite_handler.commit()

        sqlite_handler.commit()

        for doc_id in doc_index:
            sqlite_handler.insert_doc_entry(doc_id, doc_index[doc_id]['length'])

        sqlite_handler.commit()
    except IntegrityError:
        sqlite_handler.rollback()
        print '[ERROR] Cannot save index because the database file is not empty'

    sqlite_handler.close_connection()


def print_full(index_file):
    """
    prints the inverted index to STDOUT exactly
    as mentioned in the assignment. It first loads the index from
    the sqlite database and then print it.
    :param index_file:
    :return:
    """
    if not exists(index_file):
        print '%s[ERROR] The input file %s does not exist%s' % (RED, index_file, NC)
        return

    sqlite_handler = ClustererSQLiteHandler(index_file)
    try:
        inverted_index = sqlite_handler.load_index()

        for term in sorted(inverted_index.keys()):
            print "%s\t" % term,

            postings_list = inverted_index[term]['postings']

            print ";".join([str(doc) for doc in sorted(postings_list.keys())])
    except OperationalError:
        print "%s[ERROR] Tables in input database file doesn't match with the supported schema of the inverted index%s" % (
        RED, NC)
    except DatabaseError:
        print "%s[ERROR] Input file is not recognized as a SQLite database file%s" % (RED, NC)


if __name__ == "__main__":
    # inverted_index = create('../../../test_dataset')
    # save(inverted_index, '../test_dataset.db')
    print_full('../output.db')
