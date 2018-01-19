#
# CMPUT397 started code for programming assignment 1
#
# this module provides starter code with stubs of the
# functions to score keyword queries
#

from nltk.tokenize import word_tokenize
from index.load_inverted_index import *
import database.sqlite_handler as sqlite_handler
import util.analyzer as analyzer

import math

index_file = ''

''' 
Implements the algorithm in Fig 6.14 of the textbook

NOTES: 

1. the code below is hard-coded for the running example; you
   should take it as a starting point only

2. the way IDF is computed (Eq. 6.7 on pg 108) is not robust
   to terms that appear in the whole corpus. FIX THIS.

3. The algorithm on Fig 6.14 DOES NOT normalize the vector
   based on the query vector, for efficiency. Thus scores
   can be higher than 1.0 !!!
'''
def cosineScore(index, query):
    #
    # TODO: FIX ME, SO I WORK FOR MORE THAN THE EXAMPLE ONLY
    #
    if not index_file:
        Length_Vector = get_document_length_vector_test(index)
    else:
        Length_Vector = get_document_length_vector(index)

    CORPUS_SIZE = len(Length_Vector)

    Scores = {}
    for term in query:
        if term not in index:
            continue

        w_t_q = math.log(1.0 * CORPUS_SIZE / (index[term]['df'])) # compute idf of the query term, tf(query)=1
        # we skip terms in the query that have idf=0
        if w_t_q == 0:
            continue

        for doc in index[term]['postings']:
            if doc in Scores:
                # the starter code has been modified to work with the inverted index
                Scores[doc] += index[term]['postings'][doc]['tf'] * w_t_q * w_t_q
            else:
                Scores[doc] = index[term]['postings'][doc]['tf'] * w_t_q * w_t_q
    answer = []
    for doc in Scores:
        answer.append((doc, Scores[doc] / Length_Vector[doc]))
    return answer


'''
returns a vector with the 'length' of the documents
as in the algorithm of Fig 6.14. This is now done
by traversing the inverted index. This is inefficient!

TODO: change this so that you compute the vector once and
store it for future calls.
'''

'''
returns the vector that contains the length of all documents
'''

def get_document_length_vector(index):
    conn, cursor = sqlite_handler.open_connection(index_file)

    if not sqlite_handler.is_document_length_exists(cursor):
        sqlite_handler.create_document_length_table(cursor)

        N = sqlite_handler.get_number_of_documents(cursor)

        doc_word_map = {}
        for term in index:

            idf = math.log(1.0 * N / index[term]['df'])

            for doc in index[term]['postings']:
                if doc not in doc_word_map:
                    doc_word_map[doc] = {term: index[term]['postings'][doc]['tf'] * idf * 1.0}
                else:
                    doc_word_map[doc][term] = index[term]['postings'][doc]['tf'] * idf * 1.0

        vector = {}

        for doc in doc_word_map:
            Sum = 1.0
            for term in doc_word_map[doc]:
                #
                # IMPORTANT: the way the idf is computed in Eq 6.7 (pg 108)
                # does not account for terms that appear in every document
                # and thus have idf 0. We must skip them here.
                #
                Sum += doc_word_map[doc][term] * doc_word_map[doc][term]

            vector[doc] = math.sqrt(Sum)
            sqlite_handler.insert_document_length(cursor, doc, vector[doc])

        sqlite_handler.commit(conn)

    else:
        vector = sqlite_handler.load_document_length(cursor)

    sqlite_handler.close_connection(conn)

    return vector

'''
returns the vector that contains the length of documents
provided in the started code for testing
'''

def get_document_length_vector_test(index):
    N = 4
    doc_word_map = {}
    for term in index:

        idf = math.log(1.0 * N / index[term]['df'])

        for doc in index[term]['postings']:
            if doc not in doc_word_map:
                doc_word_map[doc] = {term: index[term]['postings'][doc]['tf'] * idf * 1.0}
            else:
                doc_word_map[doc][term] = index[term]['postings'][doc]['tf'] * idf * 1.0

    vector = {}

    for doc in doc_word_map:
        Sum = 1.0
        for term in doc_word_map[doc]:

            Sum += doc_word_map[doc][term] * doc_word_map[doc][term]
        vector[doc] = math.sqrt(Sum)

    return vector
'''
retrieves documents using vector space model
'''
def retrieve_documents(k, show_scores, raw_query):
    index = sqlite_handler.load_index(index_file)

    tokens = word_tokenize(raw_query)
    query = []
    for token in tokens:
        try:
            query.append(analyzer.normalize(token)) # apply normalization to tokens
        except Warning:
            pass

    scores = cosineScore(index, query)
    scores.sort(key=lambda x: x[1], reverse=True)

    topK = min(k, len(scores))
    return scores[0:topK] if show_scores else [s[0] for s in scores[0:topK]]

'''
this method is for testing our cosine similarity implementation
with the hard coded inverted index
'''
def retrieve_documents_test(k, show_scores, raw_query):
    index = get_hard_coded_inverted_index()

    query = word_tokenize(raw_query)

    scores = cosineScore(index, query)
    scores.sort(key=lambda x: x[1], reverse=True)

    topK = min(k, len(scores))
    return scores[0:topK] if show_scores else [s[0] for s in scores[0:topK]]

'''
compares the scores computed manually and the scores provided
by the algorithm
'''
def test_vector_space_query(k,query, expected_result):
    actual_result = retrieve_documents_test(k, True, query)

    test_passed = True
    for i, doc in enumerate(actual_result):
        expected_doc = expected_result[i]
        if expected_doc[0] != doc[0]:
            test_passed = False
            break

        if math.fabs(expected_doc[1] - doc[1]) > 0.001:
            test_passed = False
            break

    return test_passed

'''
WRITE YOUR UNIT TESTS HERE
'''
if __name__ == "__main__":
    # index = get_hard_coded_inverted_index()

    # simple test queries
    # queries = [tuple(["system","retrieval"]), tuple(["a", "the"]), tuple(["recall"])]

    # for query in queries:
    #     print "query: %s"%str(query)
    #     scores = cosineScore(index, query)
    #     scores.sort(key=lambda x: x[1], reverse=True)
    #     print "answer: %s"%str(scores)[1:-1]
    #     print



    #
    # Since our inverted index is huge, it is extremely hard to test it
    # manually. Subsequently, we used the hard coded inverted index provided in
    # the starter code to test manually the computation of vector space model score.
    #

    # Unit tests

    if test_vector_space_query(k=2,query='indexing increases', expected_result=[('doc3', 0.590), ('doc4', 0.347)]):
        print "pass test 1"
    else:
        print "fail test 1"

    if test_vector_space_query(k=3, query='boolean query and stemming', expected_result=[('doc4', 0.347), ('doc2', 0.198), ('doc1', 0.198)]):
        print "pass test 2"
    else:
        print "fail test 2"

    if test_vector_space_query(k=1, query='boolean query and stemming', expected_result=[('doc4', 0.347)]):
        print "pass test 3"
    else:
        print "fail test 3"

    if test_vector_space_query(k=4, query='boolean query and stemming, vocabulary', expected_result=[('doc3', 0.590), ('doc4', 0.347), ('doc2', 0.198), ('doc1', 0.198)]):
        print "pass test 4"
    else:
        print "fail test 4"

    #print retrieve_documents_test(4, True, "boolean query and stemming")