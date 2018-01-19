# Zone Scoring, Clustering and Classification

This program builds an inverted index for zone indexing and scoring. It allows also to cluster and classify documents.

In this assignment, we applyied the same tokenization techniques as in the previous assignment. See the previous README file for further details 

## Zone Scoring

This program performs weighted zone scoring. It takes a boolean query as input and retrieve the top k documents ranked according to equation 6.2 in IR book. To be able to retrieve efficiently topK documents, we build a zone index in which the zone is encoded in the postings lists.

**Usage**

```
./create_zone_index [document dir] [index dir]
```

* *document dir:* path to the directory containing the document files.
* *index dir:* path where to store the created index

In order to rank documents, we compute a weighted zone score for each document according to the following formula :

```
 score(d, q) = g .sT(d, q) + (1− g).sB(d, q)
```

Each zone of the document contributes a Boolean value. For example, if the Boolean function is ``AND`` and both query terms are present in a zone, say 'title', ``sT(d, q)`` will have a score of 1, otherwise 0 .
However if the boolean function is ``OR``, the presence of either terms in 'title' and 'body' will assign a score of one to both ``sT(d, q)`` and ``sB(d, q)``


**Usage**
```
./zone_scorer [index dir] [k] [g] [q]
```

* *index dir:* path to the index SQlite file
* *k:* the number of documents to retrieve
* *g:*  the weight value
* *q:* the query

 *query:* 
* The full query in the commande line should be enclosed in a single quote (`'`)
* Phrase queries should be enclosed in double quotes (`"`)
* `AND` and `OR` are evaluated from left to right
* You can include as many subqueries as you like which could be enclosed in parenthesis (`( )`)
 
 **Unit Tests**

To test zone scoring, you can run the following command line :

```
PYTHONPATH=[assignment2 dir absolute path] python scorer/ranked_boolean_retrieval.py
 ```
## Document Classification

The system takes a new document as input and classifies it using the KNN classification algorithm.
It uses the weighting scheme lnc.ltc according to SMART notation and cosine similarity to compare document and query vectors.
We first create an inverted index for storing terms of the corpus and another index that stores docID and their corresponding classes.


**Usage**

```
./create_labeled_index [document dir] [index dir]
```

* *document dir:* path to the directory containing the document files
* *index dir:* path where to store the created index

In order to classify the new unseen document, we use the KNN algorithm.

**Usage**

```
./knn_classifier [index dir] [k] [q]
```
* *index dir:* path to the index directory
* *k:* k nearest neighbours
* *q:* query document

**Unit Tests**

To test classifying unseen documents, we collected 9 movies storylines from imdb.com that belong to the following categories:
drama, science fiction, animation and musical. The directory to those new documents is `` test-data/classification_query/``.
You can test KNN algorithm by running the file ``knn.py`` inside the ``classifier`` directory and the index should be built in ``assignment2`` directory : (class_index1.db)

You can run the following command line to test how well the algorithm does:

```
./create_labeled_index [data dir] class_index1.db
PYTHONPATH=[assignment2 dir absolute path] python classifier/knn.py
 ```
 
## Document Clustering
Our python implementation clusters also a document collection using the K-means clustering algorithm. We used tf-idf weighting and cosine similarity as in document classification task.

**Usage**

```
./create_index [document dir] [index dir]
```
* *document dir:* path to the directory containing the document files
* *index dir:* path where to store the created index

```
 ./k_means_clusterer [index dir] [k] [optional id_1 id_2 ... id_k]
 ```
* *index dir:* path to the index directory
* *k:* number of clusters
* *id_1 id_2 ... id_k:* the initial seeds (optional)

**Test cases**

To evaluate our implementation of k-means algorithm, we created a small dataset composed of two categories: animation and sci-fi. Performing k-means clustering with 2 proper initial seeds, i.e. one document from each category, leads to one cluster for animation documents and another one for sci-fi documents. The dataset is located in ``test-data/cluster_tiny_data``. 
You can run the following command line to test how well the algorithm does:


```
./create_index test-data/cluster_tiny_data index_tiny_cluster.db
./k_means_clusterer index_tiny_cluster.db 2  24 1
 ```



















  
  
