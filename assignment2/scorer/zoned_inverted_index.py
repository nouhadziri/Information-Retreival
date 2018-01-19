import re

from util.errors import DirectoryNotFoundError
from util.fancy import *
import util.analyzer as analyzer
from os import listdir
from os.path import isfile, join, exists
from nltk.tokenize import word_tokenize
from sqlite3 import IntegrityError, OperationalError, DatabaseError

from zoned_sqlite_handler import ZonedSQLiteHandler


def create(document_dir):
    """
    creates an inverted index given an English text corpus
    for movies. If the directory provided does not exist,
    the program will print an error. If the filenames
    in the test corpus do not match with the description,
    the program will print an error and will skip the
    document.

    :param document_dir:
    :return: local_index
    """
    if not exists(document_dir):
        raise DirectoryNotFoundError()

    local_index = {}
    for f in listdir(document_dir):
        file_path = join(document_dir, f)
        if isfile(file_path):

            matched_doc_id = re.search('\d+', f)
            if matched_doc_id is None:
                print '[WARNING] The file name does not match with the description: %s' % f
                continue

            matched_doc_id_group = matched_doc_id.group()
            doc_id = int(matched_doc_id_group)

            with open(file_path, 'r') as doc:
                word_counter = 0
                for i, line in enumerate(doc):
                    zone = "title" if i == 0 else "body"

                    words = word_tokenize(line.decode('utf-8'))  # tokenize the document using NLTK tokenizer
                    for word in words:
                        try:
                            term = analyzer.normalize(word)  # applies stemming, drops stop words
                            # converts to lower case and removes punctuation

                            word_counter += 1

                            # if the term is already in the index then update its postings list
                            if term in local_index:
                                # if the document exists already in the postings list then update
                                # the term frequency and the positional index
                                if doc_id in local_index[term]['postings']:
                                    if zone in local_index[term]['postings'][doc_id]:
                                        local_index[term]['postings'][doc_id][zone]['pos'] += [word_counter]
                                    else:
                                        local_index[term]['postings'][doc_id][zone] = {'pos': [word_counter]}
                                # if the document does not exist in the postings list, add it to the postings list
                                else:
                                    local_index[term]['postings'][doc_id] = {zone: {'pos': [word_counter]}}
                            # if the term does not exist in the inverted index
                            else:
                                local_index[term] = {'postings': {doc_id: {zone: {'pos': [word_counter]}}}}
                        except Warning:
                            continue

    return local_index


def save(inverted_index, output_file):
    """
    saves the inverted index in a sqlite database
    :param inverted_index:
    :param output_file:
    :return:
    """

    if inverted_index is None:
        return

    sqlite_handler = ZonedSQLiteHandler(output_file)
    sqlite_handler.create_index_tables()

    try:
        term_id = 1
        for term in inverted_index:
            sqlite_handler.insert_index_entry(term_id, term, inverted_index[term]['postings'])
            term_id += 1

            if term_id % 1000 == 0:
                sqlite_handler.commit()

        sqlite_handler.commit()
    except IntegrityError:
        sqlite_handler.rollback()
        print '[ERROR] Cannot save index because the database file is not empty'

    sqlite_handler.close_connection()


def print_full(index_file):
    """
    prints the inverted index. It first loads the index from
    the sqlite database and then print it.

    :param index_file:
    :return:
    """
    if not exists(index_file):
        print '%s[ERROR] The input file %s does not exist%s' % (RED, index_file, NC)
        return

    try:
        sqlite_handler = ZonedSQLiteHandler(index_file)
        index = sqlite_handler.load_index()

        for term in sorted(index.keys()):
            print "%s\t" % term,

            postings_list = index[term]['postings']

            for doc in postings_list:
                for zone in postings_list[doc]:
                    print "%d.%s:%s ;" % (
                        doc, zone, ",".join([str(pos) for pos in sorted(postings_list[doc][zone]['pos'])])),

            print

    except OperationalError:
        print "%s[ERROR] Tables in input database file doesn't match with the supported schema of the inverted index%s" % (
            RED, NC)
    except DatabaseError:
        print "%s[ERROR] Input file is not recognized as a SQLite database file%s" % (RED, NC)


if __name__ == "__main__":
    # inverted_index = create('../assignment2-data/zone_data')
    # save(inverted_index, '../dataset.db')
    print_full('../dataset.db')
