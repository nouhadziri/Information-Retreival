import re

from database import sqlite_handler
from util.fancy import *
import util.analyzer as analyzer
from os import listdir
from os.path import isfile, join, exists
from nltk.tokenize import word_tokenize
from sqlite3 import IntegrityError, OperationalError, DatabaseError


'''
creates an inverted index given an English text corpus
for movies. If the directory provided does not exist,
the program will throw an error. If the filenames
in the test corpus do not match with the description,
the program will throw an error and will skip the
document.
'''

def create(document_dir):
    if not exists(document_dir):
        print '[ERROR] The directory does not exist: %s' % document_dir
        return None

    local_index = {}
    for f in listdir(document_dir):
        file_path = join(document_dir, f)
        if isfile(file_path):

            matched_doc_id = re.search('doc_\d+_', f)
            if matched_doc_id is None:
                print '[WARNING] The file name does not match with the description: %s' % f
                continue

            matched_doc_id_group = matched_doc_id.group()
            doc_id = int(matched_doc_id_group[matched_doc_id_group.find('_')+1:-1])


            with open(file_path, 'r') as doc:
                word_counter = 0
                for line in doc:
                    words = word_tokenize(line.decode('utf-8')) # tokenize the document using NLTK tokenizer
                    for word in words:
                        try:
                            term = analyzer.normalize(word) # applies stemming, drops stop words
                                                            # converts to lower case and removes punctuation

                            word_counter += 1

                            # if the term is already in the index then update its postings list
                            if term in local_index:
                                  # if the document exists already in the postings list then update
                                  # the term frequency and the positional index
                                if doc_id in local_index[term]['postings']:
                                    local_index[term]['postings'][doc_id]['tf'] += 1
                                    local_index[term]['postings'][doc_id]['pos'] += [word_counter]
                                # if the document does not exist in the postings list, add it to the postings list
                                else:
                                    local_index[term]['postings'][doc_id] = {'tf': 1, 'pos': [word_counter]}
                                    local_index[term]['df'] += 1
                            # if the term does not exist in the inverted index
                            else:
                                local_index[term] = {'postings': {doc_id: {'tf': 1, 'pos': [word_counter]}}, 'df': 1}
                        except Warning:
                            continue


    return local_index

'''
saves the inverted index in a sqlite database
'''
def save(inverted_index, output_file):
    if inverted_index is None:
        return

    conn, cursor = sqlite_handler.open_connection(output_file)
    sqlite_handler.create_index_tables(cursor)

    try:
        term_id = 1
        for term in inverted_index:
            sqlite_handler.insert_index_entry(cursor, term_id, term, inverted_index[term]['postings'], inverted_index[term]['df'])
            term_id += 1

            if term_id % 1000 == 0:
                sqlite_handler.commit(conn)

        sqlite_handler.commit(conn)
    except IntegrityError:
        sqlite_handler.rollback(conn)
        print '[ERROR] Cannot save index because the database file is not empty'

    sqlite_handler.close_connection(conn)

'''
prints the inverted index to STDOUT exactly
as mentioned in the assignment. It first loads the index from
the sqlite database and then print it.
'''
def print_full(index_file):
    if not exists(index_file):
        print '%s[ERROR] The input file %s does not exist%s' % (RED,index_file,NC)
        return

    try:
        index = sqlite_handler.load_index(index_file)

        for term in sorted(index.keys()):
            print "%s\t" % term,

            postings_list = index[term]['postings']

            print ";".join("%d:%s" % \
                      (doc, ",".join([str(pos) for pos in postings_list[doc]['pos']]))
                           for doc in sorted(postings_list.keys()))
    except OperationalError:
        print "%s[ERROR] Tables in input database file doesn't match with the supported schema of the inverted index%s" % (RED, NC)
    except DatabaseError:
        print "%s[ERROR] Input file is not recognized as a SQLite database file%s" % (RED, NC)

if __name__ == "__main__":
    # inverted_index = create('../../../test_dataset')
    # save(inverted_index, '../test_dataset.db')
    print_full('../output.db')