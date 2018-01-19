import heapq
import math
from collections import defaultdict

import labeled_inverted_index
from labeled_sqlite_handler import LabeledSQLiteHandler


class NearestNeighborClassifier(object):
    def __init__(self, index_file, k):
        self.k = k
        self.index_file = index_file
        self.inverted_index, self.doc_index = self.__load_indexes()

    def __load_indexes(self):
        sqlite_handler = LabeledSQLiteHandler(self.index_file)
        inverted_index = sqlite_handler.load_index()
        doc_index = sqlite_handler.load_doc_index()
        sqlite_handler.close_connection()
        return inverted_index, doc_index

    def classify(self, query_file):

        '''
    Takes a new document as input and classifies it using the KNN classification algorithm
    we use the weighting scheme lnc.ltc according to SMART notation and cosine similarity
    For document: log-weighted term frequency, no idf, and cosine normalization
    For query vector: log-weighted term frequency, idf weighting, and cosine normalization
        :param query_file: 
        :return: the predicted class
        '''
        N = len(self.doc_index)
        scores = defaultdict(float) #dictionary

        #create an inverted index to store tokens of the query document
        query_index = {}
        with open(query_file, 'r') as query_doc:
            for line in query_doc:
                labeled_inverted_index.create_index_per_line('q', line, query_index)

        for term in query_index:
            if term not in self.inverted_index:
                continue

            idf = math.log(1.0 * N / (self.inverted_index[term]['df']))

            for doc_id in self.inverted_index[term]['postings']:
                scores[doc_id] += (1 + math.log(self.inverted_index[term]['postings'][doc_id]['tf'])) * \
                                  (1 + math.log(query_index[term]['postings']['q']['tf'])) * idf / \
                                  self.doc_index[doc_id]['length']

        k_min_heap = self.__find_nearest(scores)
        return self.__predict_class(k_min_heap)

    def __find_nearest(self, scores):
        k_min_heap = []
        for doc in scores:
            if len(k_min_heap) < self.k:
                heapq.heappush(k_min_heap, (scores[doc], doc))
            elif scores[doc] >= min(k_min_heap)[0]:
                heapq.heappushpop(k_min_heap, (scores[doc], doc))
        return k_min_heap

    def __predict_class(self, max_heap):
        class_count = defaultdict(int)
        for (score, doc) in max_heap:
            class_count[self.doc_index[doc]['class']] += 1

        max_count = max(class_count.items(), key=lambda x: x[1])[1]
        return [clazz for clazz in class_count if class_count[clazz] == max_count]

'''
Test cases for classification
'''
def test_classification_1():

    input_index = 'class_index1.db'
    doc_query = 'test-data/classification_query/toy_story_2.txt'
    expected_class = ['Animation']

    actual_class = NearestNeighborClassifier(input_index, 4).classify(doc_query)
    print "PASS test_Knn_1" if expected_class == actual_class else "FAIL test_knn 1"


def test_classification_2():

    input_index = 'class_index1.db'
    doc_query = 'test-data/classification_query/matrix_reloaded.txt'
    expected_class = ['Sci-Fi']

    actual_class = NearestNeighborClassifier(input_index, 10).classify(doc_query)
    print "PASS test_Knn_2" if expected_class == actual_class else "FAIL test_knn 2"


def test_classification_3():

    input_index = 'class_index1.db'
    doc_query = 'test-data/classification_query/high_school_musical.txt'
    expected_class = ['Musical']

    actual_class = NearestNeighborClassifier(input_index, 10).classify(doc_query)
    print "PASS test_Knn_3" if expected_class == actual_class else "FAIL test_knn 3"

'''
WRITE YOUR UNIT TESTS HERE
'''
if __name__ == "__main__":
    test_classification_1()
    test_classification_2()
    test_classification_3()


