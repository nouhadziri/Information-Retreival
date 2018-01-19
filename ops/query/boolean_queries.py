#
# CMPUT397 started code for programming assignment 1
#
# this module provides starter code with stubs of the
# functions to answer boolean queries
#

from nltk.tokenize import word_tokenize

import database.sqlite_handler as sqlite_handler
import util.analyzer as analyzer
from parser import Parser, ParseException

index_file = ''

'''
Evaluates a boolean query as discussed in Chapters 1 and 2

Assumes the query is already optimized.

INPUT: tuple representing tree node:
   ('KEYWORD', keyword)
   ('PHARSE', "keyword_1 ... keyword_n")
   ('AND'/'OR', operand_1, operand_2)

Goes through each node, starting the recursion on the
"leftmost" operand if applicable.
'''

def evaluate_boolean_query(node):
    if node[0] == 'KEYWORD':
        return evaluate_keyword(node[1])
    elif node[0] == 'PHRASE':
        return evaluate_phrase(node[1])
    elif node[0] == 'AND':
        l1 = evaluate_boolean_query(node[1])
        l2 = evaluate_boolean_query(node[2])
        return evaluate_intersect(l1, l2)
    elif node[0] == 'OR':
        l1 = evaluate_boolean_query(node[1])
        l2 = evaluate_boolean_query(node[2])
        return evaluate_union(l1, l2)
    else:
        raise Exception("*** UNRECOGNIZED QUERY NODE: " + str(node))

'''
returns the intersection of two postings lists
'''

def evaluate_intersect(postings1, postings2):

    if not postings1 or not postings2:
        return []

    # s = time.time()
    p1 = 0
    p2 = 0

    result = []

    while p1 < len(postings1) and p2 < len(postings2):
        doc1 = postings1[p1]
        doc2 = postings2[p2]

        if doc1 < doc2:
            p1 += 1
        elif doc1 > doc2:
            p2 += 1
        else:
            result += [doc1]
            p1 += 1
            p2 += 1

    # e = time.time()
    # print "intersect %.5f" % (e - s)
    return result


'''
returns the union of two postings lists
'''

def evaluate_union(postings1, postings2):
    p1 = 0
    p2 = 0

    result = []

    while p1 < len(postings1) or p2 < len(postings2):
        if p1 < len(postings1) and p2 < len(postings2):
            doc1 = postings1[p1]
            doc2 = postings2[p2]

            if doc1 < doc2:
                result += [doc1]
                p1 += 1
            elif doc1 > doc2:
                result += [doc2]
                p2 += 1
            else:
                result += [doc1]
                p1 += 1
                p2 += 1
        elif p1 < len(postings1):
            result += [postings1[p1]]
            p1 += 1
        else:
            result += [postings2[p2]]
            p2 += 1

    return result

'''
returns two postings lists of a phrase query
'''
def evaluate_phrase(phrase):
    words = word_tokenize(phrase)
    phrase_terms = []
    for word in words:
        try:
            term = analyzer.normalize(word)
            phrase_terms += [term]
        except Warning:
            pass

    index = sqlite_handler.load_positional_index(index_file, phrase_terms)
    postings = []  # storing postings lists of all terms in a single list
    for term in phrase_terms:
        postings += [sorted(index[term]['postings'].keys()) if term in index else []]
    result = postings[0]
    for i, term in enumerate(phrase_terms):
        #if the phrase is only one term then return its postings list
        if i == 0:
            continue

        ptr1 = 0
        ptr2 = 0

        current_result = []

        while ptr1 < len(result) and ptr2 < len(postings[i]):
            doc1 = result[ptr1]
            doc2 = postings[i][ptr2]

            if doc1 < doc2:
                ptr1 += 1
            elif doc1 > doc2:
                ptr2 += 1
            else:
                pp1 = index[phrase_terms[i - 1]]['postings'][doc1]['pos']
                pp2 = index[term]['postings'][doc2]['pos']

                match_found = False
                for pos1 in pp1:
                    for pos2 in pp2:
                        if pos2 - pos1 == 1:
                            match_found = True
                            break

                    if match_found:
                        break

                if match_found:
                    current_result += [doc1]

                ptr1 += 1
                ptr2 += 1

        result = current_result

    return result


def evaluate_keyword(keyword):
    try:
        # s = time.time()
        query_term = analyzer.normalize(keyword)
        answer = tuple(sqlite_handler.load_postings_list(index_file, query_term))
        # e = time.time()
        # print "keyword time '%s' %.5f / %d" % (keyword, e - s, len(answer))
        return answer
    except Warning:
        return ()


'''
Parses a boolean query and returns a query tree.

INPUT: expression of the form:

<QUERY> :== <EXPRESSION> |
        (<QUERY>) |
        <QUERY> AND <QUERY> |
            <QUERY> OR <QUERY>
<EXPRESSION> :== <KW_EXPRESSION> | <PHRS_EXPRESSION>
<PHRS_EXPRESSION> :== "<KW_EXPRESSION>+"
<KW_EXPRESSION> :== any keyword

The parser must also tokenize the query in the same
that was used for tokenizing the corpus.
'''


def parse(expression):
    return Parser().build_ast(expression).preorder_traverse()


'''
Estimates the size of a node in a query.

INPUT: tuple representing tree node:
   ('KEYWORD', keyword)
   ('PHARSE', "keyword_1 ... keyword_n")
   ('AND'/'OR', operand_1, operand_2)
'''


def estimate_size(node):
    if node[0] == 'KEYWORD':
        term = node[1]
        return len(evaluate_keyword(term))
    elif node[0] == 'PHRASE':
        phrase = node[1]
        return len(evaluate_phrase(phrase))
    elif node[0] == 'AND':
        l1 = estimate_size(node[1])
        l2 = estimate_size(node[2])
        #
        # ASSUMPTION: the recursive query processor
        # will evaluate the sub-query in node[1] first
        #
        return l1 if l1 < l2 else l2
    elif node[0] == 'OR':
        l1 = estimate_size(node[1])
        l2 = estimate_size(node[2])
        return l1 + l2
    else:
        raise Exception("*** UNRECOGNIZED QUERY NODE: " + str(node))


'''
Goes through the query tree recursively, swapping
sublists inside AND nodes, primarily
'''


def optimize(node):
    if node[0] == 'KEYWORD' or node[0] == 'PHRASE':
        return node
    elif node[0] == 'AND':
        #
        # TODO: check this is what we really want!
        #
        l1 = estimate_size(node[1])
        l2 = estimate_size(node[2])
        return node if l1 < l2 else ('AND', optimize(node[2]), optimize(node[1]))
    elif node[0] == 'OR':
        #
        # TODO: check this is what we really want!
        #
        return ('OR', optimize(node[1]), optimize(node[2]))
    else:
        raise Exception("*** UNRECOGNIZED QUERY NODE: " + str(node))

    return node

## Test cases for parsing the query##

def test_parse_query1():
    raw_query = '(view AND user) AND snowboard'
    expected_parse_tree = ('AND', ('AND', ('KEYWORD', 'view'), ('KEYWORD', 'user')), ('KEYWORD', 'snowboard'))

    actual_parse_tree = parse(raw_query)
    print "PASS test_parse_case 1" if expected_parse_tree == actual_parse_tree else "FAIL test_case 1"


def test_parse_query2():
    raw_query = '(view AND user) AND snowboard OR serbia'
    expected_parse_tree = ('OR', ('AND', ('AND', ('KEYWORD', 'view'), ('KEYWORD', 'user')), ('KEYWORD', 'snowboard')), ('KEYWORD', 'serbia'))

    actual_parse_tree = parse(raw_query)

    print "PASS test_parse_case 2" if expected_parse_tree == actual_parse_tree else "FAIL test_case_2"

def test_parse_query3():
    raw_query = '((view AND user AND snowboard) OR (serbia))'
    expected_parse_tree =('OR', ('AND', ('AND', ('KEYWORD', 'view'), ('KEYWORD', 'user')), ('KEYWORD', 'snowboard')), ('KEYWORD', 'serbia'))

    actual_parse_tree = parse(raw_query)
    print "PASS test_parse_case 3" if expected_parse_tree == actual_parse_tree else "FAIL test_case_3"


def test_parse_query4():
    raw_query = '(view AND user AND snowboard  OR )'
    try:
        parse(raw_query)
        print "FAIL test_parse_case_4"
    except ParseException:
        print "PASS test_parse_case_4"

def test_parse_query5():
    raw_query = '((view AND user AND snowboard) OR "English Army" )'
    expected_parse_tree =('OR', ('AND', ('AND', ('KEYWORD', 'view'), ('KEYWORD', 'user')), ('KEYWORD', 'snowboard')), ('PHRASE', 'English Army'))
    actual_parse_tree = parse(raw_query)
    print "PASS test_parse_case 5" if expected_parse_tree == actual_parse_tree else "FAIL test_case_5"

def test_parse_query6():
    raw_query = 'democracy'
    expected_parse_tree = ('KEYWORD', 'democracy')
    actual_parse_tree= parse(raw_query)
    print "PASS test_parse_case 6" if expected_parse_tree == actual_parse_tree else "FAIL test_case_6"

def test_parse_query7():
    raw_query = '"English army" AND (music AND open) OR (democracy)'
    expected_parse_tree= ('OR', ('AND', ('PHRASE', 'English army'), ('AND', ('KEYWORD', 'music'), ('KEYWORD', 'open'))),
                      ('KEYWORD', 'democracy'))
    actual_parse_tree= parse(raw_query)
    print "PASS test_parse_case 7" if expected_parse_tree == actual_parse_tree else "FAIL test_case_7"

def test_parse_query8():
    raw_query = ' English army AND (music OR democracy)'
    try:
        parse(raw_query)
        print "FAIL test_case_8"
    except ParseException:
        print "PASS test_case_8_phrase_query"



## Test cases for removing stop words from the query ###

def remove_stop_words1():
    raw_query =' democracy AND the OR "english army"'
    actual_parse_stopwords = parse(raw_query)
    expected_parse_stopwords = ('OR', ('KEYWORD', 'democracy'), ('PHRASE', 'english army'))
    print "PASS test_case1_stopwords" if actual_parse_stopwords == expected_parse_stopwords else "FAIL test_case1_stopwords"

def remove_stop_words2():
    raw_query =' democracy AND the OR "english army" AND while'
    actual_parse_stopwords = parse(raw_query)
    expected_parse_stopwords = ('OR', ('KEYWORD', 'democracy'), ('PHRASE', 'english army'))
    print "PASS test_case2_stopwords" if actual_parse_stopwords == expected_parse_stopwords else "FAIL test_case2_stopwords"


def remove_stop_words3():
    raw_query =' the OR while AND "english army" AND democracy '
    actual_parse_stopwords = parse(raw_query)
    expected_parse_stopwords = ('AND', ('PHRASE', 'english army'), ('KEYWORD', 'democracy'))
    print "PASS test_case3_stopwords" if actual_parse_stopwords == expected_parse_stopwords else "FAIL test_case3_stopwords"


##Test cases for evaluating the query

def test_evaluate():

    print "*** TEST CASE: Evaluate 1 ***\n "

    raw_query1 = 'occupation AND technique  AND  democracy'
    actual_optimizing_result1= optimize(parse(raw_query1))
    expected_optimizing_result1 = ('AND', ('KEYWORD', 'democracy'), ('AND', ('KEYWORD', 'technique'), ('KEYWORD', 'occupation')))
    expected_result1 = [5]
    actual_parsing_result1 = evaluate_boolean_query(optimize(parse(raw_query1)))
    print "PASS test_case_optimize 1" if actual_optimizing_result1 == expected_optimizing_result1 else "FAIL test_case_optimize_1"
    print "PASS test_case_evaluate 1" if actual_parsing_result1 == expected_result1 else "FAIL test_case_1"

    print "\n "

    print "*** TEST CASE 2: Evaluate 2  *** \n "

    raw_query2 = 'one AND open AND music'
    actual_optimizing_result2 = optimize(parse(raw_query2))
    expected_optimizing_result2 =('AND', ('KEYWORD', 'music'), ('AND', ('KEYWORD', 'open'), ('KEYWORD', 'one')))
    expected_result2 = [0, 9, 92, 99, 230, 293, 305, 381, 409, 410, 439, 507, 529, 600, 722, 723, 725, 726, 741, 958, 1073, 1251, 1262, 1322, 1415, 1419, 1485, 1487, 1526, 1538, 1618, 1697, 1717, 1725, 1764, 1865, 1921, 1994]
    actual_evaluate_result2= evaluate_boolean_query(optimize(parse(raw_query2)))
    print "PASS test_case_optimize 2" if expected_optimizing_result2 == actual_optimizing_result2 else "FAIL test_case_optimize2"
    print "PASS test_case_evaluate 2" if actual_evaluate_result2 == expected_result2 else "FAIL test_case_evaluate2"

    print "\n "

    print "*** TEST CASE 3: Evaluate 3  *** \n "

    raw_query3 = ' leader AND england AND "Home Guard" '
    actual_optimizing_result3 = optimize(parse(raw_query3))
    expected_optimizing_result3 = ('AND', ('PHRASE', 'Home Guard'), ('AND', ('KEYWORD', 'england'), ('KEYWORD', 'leader')))
    actual_evaluate_result3= evaluate_boolean_query(optimize(parse(raw_query3)))
    expected_result3 = [1629]
    print "PASS test_case_optimize 3" if actual_optimizing_result3 == expected_optimizing_result3 else "FAIL test_case_optimize3"
    print "PASS test_case_evaluate 3" if actual_evaluate_result3 == expected_result3 else "FAIL test_case_evaluate3"

    print "\n "

    print "*** TEST CASE 4: Evaluate 4 *** \n "

    raw_query4 = "democracy AND occupation AND open OR neural"
    actual_evaluate_result4 = evaluate_boolean_query(parse(raw_query4))
    expected_result4= [1346, 1916]
    print "PASS test_case_evaluate 4" if actual_evaluate_result4 == expected_result4 else "FAIL test_case_4"

    print "*** TEST CASE 5: Evaluate 5 ***\n "

    raw_query5 = 'democracy AND occupation AND open OR "English Army"'
    actual_evaluate_result5 = evaluate_boolean_query(parse(raw_query5))
    expected_result5 = [275,712,1716]
    print "PASS test_case_evaluate5" if actual_evaluate_result5 == expected_result5 else "FAIL test_case_5"

    print "\n "


'''
WRITE YOUR UNIT TESTS HERE
'''
if __name__ == "__main__":

    index_file = '../output.db'

    test_parse_query1()
    test_parse_query2()
    test_parse_query3()
    test_parse_query4()
    test_parse_query5()
    test_parse_query6()
    test_parse_query8()

    test_evaluate()
    remove_stop_words1()
    remove_stop_words2()
    remove_stop_words3()






