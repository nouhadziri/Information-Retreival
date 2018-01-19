import math
import random
import sys
from collections import defaultdict
from operator import add

from clusterer_sqlite_handler import ClustererSQLiteHandler


class KMeansClusterer(object):
    def __init__(self, index_file, k, seeds):
        self.k = k
        self.index_file = index_file

        # We use two indexes: one for document terms and one for document to compute the length
        # doc_tfidf_vector is computed using both indexes
        # the seeds should be docID because the initial points are documents
        self.inverted_index, self.doc_index, self.doc_tfidf_vector = self.__load_indexes()
        if seeds:
            self.seeds = seeds
            # check whether the docID exists in the doc_index, otherwise throw an exception
            non_existing_seeds = [s for s in seeds if s not in self.doc_index]
            if non_existing_seeds:
                raise Exception('the documents provided as seeds does not exist in the dataset: %s' % non_existing_seeds)
        else:
            key_indices = random.sample(range(len(self.doc_index)), k)
            self.seeds = [doc_id for i, doc_id in enumerate(self.doc_index.keys()) if i in key_indices]

    def __load_indexes(self):
        sqlite_handler = ClustererSQLiteHandler(self.index_file)
        inverted_index = sqlite_handler.load_index()
        doc_index = sqlite_handler.load_doc_index()
        sqlite_handler.close_connection()

        # N = len(doc_index) # corpus size
        T = len(inverted_index) # Number of tokens= size of the vocabulary, will be used for building the centroid vector

        doc_tfidf_vector = {} # a dictionary that stores all the documents vectors <docID, docVector>

        for term in inverted_index:

            term_index = inverted_index[term]['i'] # i is the term index in the inverted index

            for doc_id in inverted_index[term]['postings']:
                if doc_id not in doc_tfidf_vector:
                    doc_tfidf_vector[doc_id] = [0.0] * T
                doc_tfidf_vector[doc_id][term_index] = (1 + math.log(inverted_index[term]['postings'][doc_id]['tf']))

        return inverted_index, doc_index, doc_tfidf_vector

    def cluster(self):

        centroids = [list(self.doc_tfidf_vector[doc_id]) for doc_id in self.seeds]

        # N = len(self.doc_index)
        # for term in self.inverted_index:
        #     idf = math.log(1.0 * N / (self.inverted_index[term]['df']))
        #
        #     for centroid in centroids:
        #         centroid[self.inverted_index[term]['i']] *= idf

        w = defaultdict(list)

        while True:
            # old_w = dict(w)
            w.clear()

            for doc in self.doc_index:
                closest_centroid = (0, -1)
                for i, centroid in enumerate(centroids):
                    similarity = self.__calc_cosine_similarity(centroid, doc)
                    if similarity > closest_centroid[1]:
                        closest_centroid = (i, similarity)

                w[closest_centroid[0]].append(doc) # assign the document to the closest cluster

            # assignment_changed = False
            #
            # for new_cluster in w.values():
            #     new_sorted_cluster = sorted(new_cluster)
            #
            #     found = False
            #     for old_cluster in old_w.values():
            #         if new_sorted_cluster == sorted(old_cluster):
            #             found = True
            #             break
            #
            #     if not found:
            #         assignment_changed = True
            #         break
            #
            # if not assignment_changed:
            #     break

            centroid_changed = False

            #update the centroid: we take average from each point in the cluster
            for centroid_index in w:
                old_centroid = centroids[centroid_index]
                new_centroid = [0.0] * len(centroids[centroid_index])

                for doc in w[centroid_index]:
                    new_centroid = map(add, self.doc_tfidf_vector[doc], new_centroid) # adds two vector together

                centroids[centroid_index] = [c_val / len(w[centroid_index]) for c_val in new_centroid] # update the centroid by taking the average
                if old_centroid != centroids[centroid_index]:
                    centroid_changed = True

            if not centroid_changed:
                break

        return dict(w)

    def __calc_cosine_similarity(self, centroid, doc):
        return sum([centroid[i] * self.doc_tfidf_vector[doc][i] for i in range(0, len(centroid))]) / \
               (self.doc_index[doc]['length'] * math.sqrt(sum([c_val ** 2 for c_val in centroid])))



'''
Test cases for clustering
'''
def test_clustering_1():

    input_index = '../index_tiny_cluster.db'
    expected_clusters = [[24,25], [1,2]]

    actual_clusters = KMeansClusterer(input_index, 2, [24, 1]).cluster()

    similar_clusters = True
    for cluster_index, cluster in actual_clusters.items():
        if cluster not in expected_clusters:
            similar_clusters = False
            break

    print "PASS test_Kmeans_1" if similar_clusters else "FAIL test_kmeans1"



'''
WRITE YOUR UNIT TESTS HERE
'''
if __name__ == "__main__":
    test_clustering_1()

