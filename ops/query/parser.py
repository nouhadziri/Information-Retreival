import re

from tree import BinaryTree
from util.analyzer import is_stopword
from nltk.tokenize import word_tokenize

class Parser:

    ##
    ## tokenize the query into tokens
    ##
    def __tokenize(self, expression):

        #tokenize the query using NLTK tokenizer
        raw_tokenized_expression = word_tokenize(expression)

        quote_begins = False
        phrase = ''

    # deals with phrase query : it merges the terms enclosed in double quotes (")
        tokenized_expression = []
        for token in raw_tokenized_expression:
            if token in ['\'\'', '"', '``']:
                if quote_begins:
                    tokenized_expression.append('"%s"' % phrase.strip())
                    phrase = ''
                    quote_begins = False
                else:
                    quote_begins = True
            elif quote_begins:
                phrase += ' ' + token
            else:
                tokenized_expression.append(token)

        return tokenized_expression


    # processes the operator and the operand stack.
    # it builds a subtree and store it in the operand stack

    def __process(self, operator_stack, operand_stack):

        operator = operator_stack.pop()

        if operator == '(':
            return False

        operand1 = operand_stack.pop()
        operand2 = operand_stack.pop()
        operator_node = BinaryTree(operator, operator)
        operator_node.add_right(operand1)
        operator_node.add_left(operand2)
        operand_stack.append(operator_node)

        return True


      # builds a syntax tree based on the query using 2 stacks :
      # one stack for storing the operands
      # and the other stack for storing operators
      # it goes through the query and whenever it encounters a token, it
      # stores it in the operand stack and if it encounters "AND", "OR", ")" or "("
      # it stores it in the operator stack. It calls process() method to process
      # the two stacks and build the final syntax tree.

    def build_ast(self, expression):
        try:
            tokenized_expression = self.__tokenize(expression)

            operator_stack = []
            operand_stack = []
            prev_token = ''

            for token in tokenized_expression:
                if token == '(':
                    operator_stack.append(token) # push "(" in the operator stack
                elif token.upper() == 'AND' or token.upper() == 'OR':
                    while operator_stack and operator_stack[-1] != '(':
                        if not self.__process(operator_stack, operand_stack): # build a subtree and store it in the operand stack
                            break

                    operator_stack.append(token.upper())
                elif token == ')':
                    while True:
                        if not self.__process(operator_stack, operand_stack):
                            break
                elif token.startswith('"'): # if we encounter a phrase, it appends it in the operand stack
                    operand_stack.append(BinaryTree('PHRASE', token[1:-1])) #substring because no need to store the quotes of the phrase
                else:
                    if prev_token and prev_token.upper() not in ('(', ')', 'AND', 'OR'):
                        raise ParseException('Invalid Expression: Missing operator')
                    operand_stack.append(BinaryTree('KEYWORD', token)) # if it is a keyword store it in the operand stack

                prev_token = token  # to handle processing phrase queries in building the tree


            while operator_stack:
                if not self.__process(operator_stack, operand_stack):
                    # if we have a missing parenthesis
                    raise ParseException('Invalid Expression: Missing ")"')

            if not operator_stack and len(operand_stack) > 1:
                # if we have an invalid expression with missing operator (e.g. A B, A B AND, AND A B OR ...)
                raise ParseException('Invalid Expression: Missing operator')

            syntax_tree = operand_stack.pop()

            syntax_tree = self.__prune_stopwords(syntax_tree, syntax_tree)

            return syntax_tree
        except IndexError:
            # handle most type of errors like A AND AND B
            raise ParseException('Invalid Expression')


    ## Since we drop stop words from the whole corpus
    ## we do the same with queries. However, it is a bit tricky removing
    ## them from the binary tree. This methods traverses the whole tree
    ## and deletes nodes that corresponds to stop words.

    ##
    ## It is a recursive algorithm. We check if there are stop words in the tree.
    ## if so, we prune left subtree or/and right subtree
    ## when pruning stop words, the node may loose the link with its children,
    ## so we use transplant_by_right() method or transplant_by_left() method
    ## to link the child node to the corresponding parent
    ##

    def __prune_stopwords(self, node, root):
        if node.node_type == 'KEYWORD' or node.node_type == 'PHRASE':
            # if the node is a stop word we nullify the node
            if is_stopword(node.node_value):
                node.nullify()
        elif node.node_type == 'AND' or node.node_type == 'OR':
            self.__prune_stopwords(node.left, root)
            self.__prune_stopwords(node.right, root)

            if node.left is None and node.right is None:
                p = node.parent
                if p is not None:
                    if p.parent is not None:
                        if p.left == node:
                            if not p.transplant_by_right():
                                p.left = None
                        else:
                            if not p.transplant_by_left():
                                p.right = None
                    else:
                        node.nullify()
                        return BinaryTree()
                else:
                    return BinaryTree()
            elif node.left is None:
                if not node.transplant_by_right():
                    return node.right
            elif node.right is None:
                if not node.transplant_by_left():
                    return node.left

        return root


class ParseException(Exception):
    def __init__(self, *args, **kwargs):
        super(ParseException, self).__init__(*args, **kwargs)