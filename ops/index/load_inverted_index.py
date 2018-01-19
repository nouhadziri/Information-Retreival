#
# CMPUT397 started code for programming assignment 1
#
# this module provides functions to load the inverted index
# from a file/directory/sqlite database

import math

from database import sqlite_handler
from os.path import exists
from sqlite3 import IntegrityError, OperationalError, DatabaseError
from util.fancy import *

''' 
returns a hard-coded inverted index from the example 
'''


def get_hard_coded_inverted_index():
    example_inverted_index = {
        'a': {'df': 3,
              'postings': {
                  'doc1': {'tf': 1, 'tf-idf': 0.1249387366, 'pos': [1]},
                  'doc2': {'tf': 1, 'tf-idf': 0.1249387366, 'pos': [1]},
                  'doc4': {'tf': 2, 'tf-idf': 0.2498774732, 'pos': [12, 20]}
              }
              },
        'at': {'df': 1,
               'postings': {
                   'doc4': {'tf': 1, 'tf-idf': 0.6020599913, 'pos': [5]}
               }
               },
        'be': {'df': 1,
               'postings': {
                   'doc4': {'tf': 1, 'tf-idf': 0.6020599913, 'pos': [3]}
               }
               },
        'boolean': {'df': 2,
                    'postings': {
                        'doc1': {'tf': 1, 'tf-idf': 0.3010299957, 'pos': [3]},
                        'doc2': {'tf': 1, 'tf-idf': 0.3010299957, 'pos': [3]}
                    }
                    },
        'but': {'df': 1,
                'postings': {
                    'doc4': {'tf': 1, 'tf-idf': 0.6020599913, 'pos': [8]}
                }
                },
        'chops': {'df': 1,
                  'postings': {
                      'doc4': {'tf': 1, 'tf-idf': 0.6020599913, 'pos': [15]}
                  }
                  },
        'ending': {'df': 1,
                   'postings': {
                       'doc4': {'tf': 1, 'tf-idf': 0.6020599913, 'pos': [18]}
                   }
                   },
        'in': {'df': 2,
               'postings': {
                   'doc1': {'tf': 1, 'tf-idf': 0.3010299957, 'pos': [1]},
                   'doc2': {'tf': 1, 'tf-idf': 0.3010299957, 'pos': [1]}
               }
               },
        'increases': {'df': 1,
                      'postings': {
                          'doc3': {'tf': 1, 'tf-idf': 0.6020599913, 'pos': [2]}
                      }
                      },
        'indexing': {'df': 1,
                     'postings': {
                         'doc4': {'tf': 1, 'tf-idf': 0.6020599913, 'pos': [6]}
                     }
                     },
        'invoked': {'df': 1,
                    'postings': {
                        'doc4': {'tf': 1, 'tf-idf': 0.6020599913, 'pos': [4]}
                    }
                    },
        'lowers': {'df': 2,
                   'postings': {
                       'doc1': {'tf': 1, 'tf-idf': 0.3010299957, 'pos': [8]},
                       'doc2': {'tf': 1, 'tf-idf': 0.3010299957, 'pos': [8]}
                   }
                   },
        'never': {'df': 2,
                  'postings': {
                      'doc1': {'tf': 1, 'tf-idf': 0.3010299957, 'pos': [7]},
                      'doc2': {'tf': 1, 'tf-idf': 0.3010299957, 'pos': [7]}
                  }
                  },
        'not': {'df': 1,
                'postings': {
                    'doc4': {'tf': 1, 'tf-idf': 0.6020599913, 'pos': [9]}
                }
                },
        'of': {'df': 1,
               'postings': {
                   'doc3': {'tf': 1, 'tf-idf': 0.3010299957, 'pos': [5]}
               }
               },
        'off': {'df': 1,
                'postings': {
                    'doc4': {'tf': 1, 'tf-idf': 0.6020599913, 'pos': [16]}
                }
                },
        'precision': {'df': 1,
                      'postings': {
                          'doc1': {'tf': 1, 'tf-idf': 0.6020599913, 'pos': [9]}
                      }
                      },
        'processing': {'df': 1,
                       'postings': {
                           'doc4': {'tf': 1, 'tf-idf': 0.6020599913, 'pos': [11]}
                       }
                       },
        'query': {'df': 1,
                  'postings': {
                      'doc4': {'tf': 1, 'tf-idf': 0.6020599913, 'pos': [13]}
                  }
                  },
        'recall': {'df': 1,
                   'postings': {
                       'doc2': {'tf': 1, 'tf-idf': 0.6020599913, 'pos': [9]}
                   }
                   },
        'retrieval': {'df': 2,
                      'postings': {
                          'doc1': {'tf': 1, 'tf-idf': 0.3010299957, 'pos': [4]},
                          'doc2': {'tf': 1, 'tf-idf': 0.3010299957, 'pos': [4]}
                      }
                      },
        'should': {'df': 1,
                   'postings': {
                       'doc4': {'tf': 1, 'tf-idf': 0.6020599913, 'pos': [2]}
                   }
                   },
        'size': {'df': 1,
                 'postings': {
                     'doc3': {'tf': 1, 'tf-idf': 0.6020599913, 'pos': [4]}
                 }
                 },
        'stemming': {'df': 4,
                     'postings': {
                         'doc1': {'tf': 1, 'tf-idf': 0, 'pos': [6]},
                         'doc2': {'tf': 1, 'tf-idf': 0, 'pos': [6]},
                         'doc3': {'tf': 1, 'tf-idf': 0, 'pos': [1]},
                         'doc4': {'tf': 2, 'tf-idf': 0, 'pos': [1, 14]}
                     }
                     },
        'system': {'df': 2,
                   'postings': {
                       'doc1': {'tf': 1, 'tf-idf': 0.3010299957, 'pos': [5]},
                       'doc2': {'tf': 1, 'tf-idf': 0.3010299957, 'pos': [5]}
                   }
                   },
        'the': {'df': 2,
                'postings': {
                    'doc3': {'tf': 2, 'tf-idf': 0.6020599913, 'pos': [3, 6]},
                    'doc4': {'tf': 1, 'tf-idf': 0.3010299957, 'pos': [17]}
                }
                },
        'time': {'df': 1,
                 'postings': {
                     'doc4': {'tf': 1, 'tf-idf': 0.6020599913, 'pos': [7]}
                 }
                 },
        'vocabulary': {'df': 1,
                       'postings': {
                           'doc3': {'tf': 1, 'tf-idf': 0.6020599913, 'pos': [7]}
                       }
                       },
        'while': {'df': 1,
                  'postings': {
                      'doc4': {'tf': 1, 'tf-idf': 0.6020599913, 'pos': [10]}
                  }
                  },
        'word': {'df': 1,
                 'postings': {
                     'doc4': {'tf': 1, 'tf-idf': 0.6020599913, 'pos': [21]}
                 }
                 }
    }
    return example_inverted_index


'''
goes through an inverted index and checks that the
df and tf values agree with the posting lists. 
 '''


def check_inverted_index(idx):
    for term in idx:
        documents = idx[term]['postings']
        if idx[term]['df'] != len(documents):
            print "*** ERROR *** 'df' for term <" + term + "> is wrong"
            print idx[term]
            return "FAIL"
        for doc in documents:
            if idx[term]['postings'][doc]['tf'] != len(idx[term]['postings'][doc]['pos']):
                print "*** ERROR *** 'tf' for term <" + term + "> is wrong"
                print idx[term]['postings'][doc]
                return "FAIL"
    return "PASS"


'''
Returns the inverted index

TODO: load the inverted index from disk 
    for now, returns a hard-coded one
'''


def get_inverted_index(index_file):
    #  index = get_hard_coded_inverted_index()

    if not exists(index_file):
        print '%s[ERROR] The input file %s does not exist%s' % (RED, index_file, NC)

    else:
        try:
            index = sqlite_handler.load_index(index_file)
            if check_inverted_index(index) == "PASS":
                return index

        except OperationalError:
            print "%s[ERROR] Tables in input database file doesn't match with the supported schema of the inverted index%s" % (
            RED, NC)
        except DatabaseError:
            print "%s[ERROR] Input file is not recognized as a SQLite database file%s" % (RED, NC)

    return None

'''
WRITE YOUR UNIT TESTS HERE
'''

def test_case_1():
    index_file = '../output.db'
    index = get_inverted_index(index_file)
    if index is None:
        print "FAIL test case 1"
    else:
        print "PASS test case 1"


def test_case_2():
    index_file = 'nonExistingFile.db'
    index = get_inverted_index(index_file)
    if index is None:
        print "PASS test case 2"
    else:
        print "FAIL test case 2"


def test_case_3():
    index_file = '../notSupportedSchema.db'
    sqlite_handler.open_connection(index_file)
    index = get_inverted_index(index_file)
    if index is None:
        print "PASS test case 3"
    else:
        print "FAIL test case 3"


if __name__ == "__main__":
    test_case_1()
    test_case_2()
    test_case_3()


