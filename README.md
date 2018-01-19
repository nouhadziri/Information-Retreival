# Boolean Retrieval and Vector Space Model

This program builds an inverted index for processing queries using Boolean Retrieval and Vector Space Model.

Preprocessing is an important task and critical step in building the inverted index. It reduces the size of indexing file and it also improves the overall efficiency and effectiveness. That's why we used different techniques for Tokenization.

## Setup
In order to run the program, you need to install the Natural language Toolkit (NLTK)

```
pip install -U nltk --user
```
You need also to download two NLTK packages for the task of tokenization and dropping stop words: punkt and stopwords.
To do so, use ``nltk.download()``


## Tokenization
The system performs the following steps:

1. Tokenizes text into individual words using NLTK.
2. Removes punctuation like (',", ^, ., etc) using python built-in function so that a search for U.S.A will also match USA and vice versa. We also deal with unicode punctuation character like (—  ‘  “  ,etc) and remove them.
2. Removes the distinction between singular and plural (e.g. dog versus dogs) or between tenses (e.g. cooking versus cooked versus cook) by stemming each word to its root form using Porter Stemmer implemented in NLTK. By doing so, recall would increase.
3. Removes commonly used words or stopwords like "the", "and", and "or". In most cases, stop words add little semantic value to a sentence. That's why we drop them. This increases performance (fewer terms in the dictionary).
4. Lowercase all tokens.

## Create index
The inverted index has been created using an English text corpus of 2000 documents about movies. This python implementation takes a directory containing the unindexed documents in the corpus as a command line argument like the following :

```
./create_index [directory]
```

* *directory:* path to the directory containing the document files. 

The command above will create the inverted index and store it on disk. In order to execute the rest of the command successfully, you have to create the inverted index (``output.db``) and use it in future calls. 

**Unit Tests**

To test loading the inverted index, we use three test cases:
 * Test case 1: checks whether the inverted index has been stored correctly or not. This test will pass if the index has been loaded successfully.
 * Test case 2: checks how the program handles a non existing index file. If the index file does not exist, the program must not throw a runtime error. 
 * Test case 3: checks whether errors in input index file are handled properly or not. For example, if the index file is not a supported SQLite file, the propram will print an error message.
 
You can test these three scenarios by running the file ``load_inverted_index.py``.

## Print index

We load the inverted index from disk into a data structure in memory and we print it using the following command :

```
./print_index [directory]
```

* *directory:* path to the SQlite file (``output.db``).
The above command will take the directory specified in the command line and will print each distinct term along with its postings lists in a single line.

## Boolean queries
This program takes a Boolean query as input and retrieve all matched documents. A Boolean query may contain the operators `AND`,`OR`, `(`, or `)` . For instance, consider the following query:

```
democracy AND (occupation OR technique)
```
Our program will parse the query and generate a syntax tree like the following :

```
`('AND', ('KEYWORD', 'democracy'), ('OR', ('KEYWORD', 'occupation'), ('KEYWORD', 'technique')))
```
To build the syntax tree, we implemented a method called `build_ast(query)` that takes the query as argument and uses two stacks: one for storing operators (`AND`, `OR`, `)`, `(` ) and the other one for storing operands (term queries).
Based on this tree, the program will be able to evaluate the query and retrieve documents.

Since we are dropping stop words from documents and queries, we addressed deleting stop words nodes from the tree as well.
To this end, we implemented a method called `prune_stopwords(self, node, root)`. This method is recursive. We check first if there are stop words in the tree. If so, we prune left subtree or/and right subtree. However, when removing stop words, the parent node may loose the link with its children, so we use `transplant_by_right()` method or `transplant_by_left()` method
to link the child node to the corresponding parent.

**Usage**

```
./boolean_query [index file] [query]
```

* *index file:* path to the SQlite file (``output.db``)

 *query:* 
* The full query in the commande line should be enclosed in a single quote (`'`)
* Phrase queries should be enclosed in double quotes (`"`)
* `AND` and `OR` are evaluated from left to right
* You can include as many subqueries as you like which could be enclosed in parenthesis (`( )`)

The program takes care of invalid query (e.g., term AND OR, missing parenthesis) and prints an error. It also prints an error if the index file do no match with the format of the inverted index implemented.
Make sure also to provide all arguments in the commande line otherwise the program will handle that by printing an error.

**Unit Tests**

To test boolean queries, we use multiple test cases for the following three scenarios:
 * scenario 1: tests parsing the query expression
 * scenario 2: tests removing stop words from the syntax tree
 * scenario 3: tests evaluating and optimizing the query

You can test these three scenarios by running the file ``boolean_queries.py``

## Vector Space Model

Our program also retrieves documents based on their relevance to the query using vector space model.
It uses the tf-idf scheme for the term weights. Our assumption is to skip terms that appear in all documents since their idf will be equal to 0.

**Usage**

```
./vs_query [index location] [k] [scores] [term_1] [term_2] … [term_n]
```
* *index location:* path to the SQlite file (``output.db``)
* *k:* the number of documents to retrieve
* *scores:*  should be either y or n
* *term:* query term

**Unit Tests**

Since our inverted index is huge, it is extremely hard to test it manually. Subsequently, we used the hard coded inverted index provided in the starter code to test manually the computation of vector space model score.

We provided 4 test cases to test the computation of vector space model score. You can test these test units by running the file ``vector_space_model.py``









