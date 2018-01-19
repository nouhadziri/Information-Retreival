'''
This program performs weighted zone scoring.
 It takes a boolean query as input and retrieve the top k documents 
 ranked according to equation 6.2 in IR book. 
'''

from parser import Parser
from util import analyzer
from zoned_sqlite_handler import ZonedSQLiteHandler
from nltk import word_tokenize

index = None
k = 0
g = 0.0


def evaluate_query(index_file, top_k, zone_weight, query):
    '''
    :param index_file: 
    :param top_k: 
    :param zone_weight: 
    :param query: 
    :return: top k results
    '''
    global index, k, g

    sqlite_handler = ZonedSQLiteHandler(index_file)
    index = sqlite_handler.load_index()
    sqlite_handler.close_connection()

    k = top_k
    g = zone_weight

    result = evaluate_expression(parse(query))
    scored_result = calc_score(result)
    scored_result.sort(key=lambda x: x[1], reverse=True)

    return scored_result[0:min(k, len(scored_result))] if scored_result else scored_result


def calc_score(matched_docs):
    '''
    Compute the weighted score for each document
    :param matched_docs: 
    :return: result
    '''
    result = []

    for (doc, zones) in matched_docs:
        s_T = 1 if 'title' in zones else 0
        s_B = 1 if 'body' in zones else 0
        result.append((doc, g*s_T + (1-g)*s_B))

    return result


def evaluate_expression(node):
    '''
    evaluate the user's query
    :param node: 
    :return: 
    '''
    if node[0] == 'KEYWORD':
        return evaluate_keyword(node[1])
    elif node[0] == 'PHRASE':
        return evaluate_phrase(node[1])
    elif node[0] == 'AND':
        return evaluate_intersect(evaluate_expression(node[1]), evaluate_expression(node[2]))
    elif node[0] == 'OR':
        return evaluate_union(evaluate_expression(node[1]), evaluate_expression(node[2]))
    else:
        raise Exception("*** UNRECOGNIZED QUERY NODE: " + str(node))


def evaluate_intersect(postings1, postings2):

    if not postings1 or not postings2:
        return []

    # s = time.time()
    p1 = 0
    p2 = 0

    result = []

    while p1 < len(postings1) and p2 < len(postings2):
        doc1 = postings1[p1][0]
        doc2 = postings2[p2][0]

        if doc1 < doc2:
            p1 += 1
        elif doc1 > doc2:
            p2 += 1
        else:
            matched_zones = [z for z in postings1[p1][1] if z in postings2[p2][1]]

            if matched_zones:
                result.append((doc1, matched_zones))

            p1 += 1
            p2 += 1

    # e = time.time()
    # print "intersect %.5f" % (e - s)
    return result



def evaluate_union(postings1, postings2):

    p1 = 0
    p2 = 0

    result = []

    while p1 < len(postings1) or p2 < len(postings2):
        if p1 < len(postings1) and p2 < len(postings2):
            doc1 = postings1[p1][0]
            doc2 = postings2[p2][0]

            if doc1 < doc2:
                result.append(postings1[p1])
                p1 += 1
            elif doc1 > doc2:
                result.append(postings2[p2])
                p2 += 1
            else:
                result.append((doc1, list(set().union(*[postings1[p1][1], postings2[p2][1]]))))
                p1 += 1
                p2 += 1
        elif p1 < len(postings1):
            result.append(postings1[p1])
            p1 += 1
        else:
            result.append(postings2[p2])
            p2 += 1

    return result


def evaluate_phrase(phrase):
    """
    evaluates phrase queries
    :param phrase:
    :return: two postings lists of a phrase query
    """

    words = word_tokenize(phrase)
    phrase_terms = []
    for word in words:
        try:
            term = analyzer.normalize(word)
            phrase_terms += [term]
        except Warning:
            pass

    postings = []  # storing postings lists of all terms in a single list
    for term in phrase_terms:
        postings += [sorted(index[term]['postings'].keys()) if term in index else []]

    result = postings[0]

    if phrase_terms[0] in index:
        zone_dict = {'title': [doc for doc, zones in index[phrase_terms[0]]['postings'].items() if 'title' in zones],
                    'body': [doc for doc, zones in index[phrase_terms[0]]['postings'].items() if 'body' in zones]}
    else:
        zone_dict = {'title': [], 'body': []}

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
                posting1 = index[phrase_terms[i - 1]]['postings'][doc1]
                posting2 = index[term]['postings'][doc2]

                for z1 in posting1:
                    for z2 in posting2:
                        if z1 == z2:
                            pp1 = posting1[z1]['pos']
                            pp2 = posting2[z2]['pos']

                            match_found = False
                            for pos1 in pp1:
                                for pos2 in pp2:
                                    if pos2 - pos1 == 1:
                                        match_found = True
                                        break

                                if match_found:
                                    break

                            if match_found:
                                current_result.append(doc1)
                                if doc1 not in zone_dict[z1]:
                                    zone_dict[z1].append(doc1)

                ptr1 += 1
                ptr2 += 1

        result = current_result
        for zone in zone_dict:
            zone_dict[zone] = [doc for doc in zone_dict[zone] if doc in result]

    result_with_zones = []
    for dt in zone_dict['title']:
        zones = ['title']
        if dt in zone_dict['body']:
            zones.append('body')
        result_with_zones.append((dt, zones))

    for db in zone_dict['body']:
        if db not in zone_dict['title']:
            result_with_zones.append((db, ['body']))

    result_with_zones.sort(key=lambda x: x[0])
    return result_with_zones


def evaluate_keyword(keyword):
    '''
    evaluate keyword queries
    :param keyword: 
    :return: 
    '''
    try:
        # s = time.time()
        answer = []
        query_term = analyzer.normalize(keyword)
        if query_term in index:
            for doc, zones in index[query_term]['postings'].items():
                answer.append((doc, zones.keys()))
        answer.sort(key=lambda x: x[0])
        return answer
    except Warning:
        return ()


def parse(query):
    return Parser().build_ast(query).preorder_traverse()



# -----------------------------------------------------------------------------------
# Test cases for zone scoring
# -----------------------------------------------------------------------------------


# both terms are in body
def test_score_query1():
    raw_query = 'Interstellar AND disasters'
    expected_reult = [(0 ,0.8)]

    actual_result = evaluate_query(index_file, 3, 0.2, raw_query)
    print "PASS test_score_case 1" if expected_reult == actual_result else "FAIL test_score_case 1"

# both terms are in body and title
def test_score_query2():
    raw_query = 'fight AND club'
    expected_reult = [(2 ,1)]

    actual_result = evaluate_query(index_file, 3, 0.2, raw_query)
    print "PASS test_score_case 2" if expected_reult == actual_result else "FAIL test_score_case 2"



# one term in the title and "phrase keyword" in body
def test_score_query3():
    raw_query = '"French chef" OR Ratatouille'
    expected_reult = [(11, 1)]

    actual_result = evaluate_query(index_file, 3, 0.2, raw_query)
    print "PASS test_score_case 3" if expected_reult == actual_result else "FAIL test_score_case 3"


# "phrase keyword" in the body
def test_score_query4():
    raw_query = '"James Gordon"'
    expected_reult = [(5,0.8)]

    actual_result = evaluate_query(index_file, 3, 0.2, raw_query)
    print "PASS test_score_case 4" if expected_reult == actual_result else "FAIL test_score_case 4"


def test_score_query5():
    raw_query = '(know AND married) OR (becomes OR dark)'
    expected_reult = [(5, 1.0),(23,1.0),(2,0.8),(4,0.8),(10,0.8),(11,0.8),(12,0.8),(17,0.8),(19,0.8),(22,0.8)]

    actual_result = evaluate_query(index_file, 10, 0.2, raw_query)
    print "PASS test_score_case 5" if expected_reult == actual_result else "FAIL test_score_case 5"



'''
WRITE YOUR UNIT TESTS HERE
'''
if __name__ == "__main__":

    index_file = 'index_zone.db'
    test_score_query1()
    test_score_query2()
    test_score_query3()
    test_score_query4()
    test_score_query5()

