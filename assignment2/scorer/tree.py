
class BinaryTree:
    def __init__(self, node_type='', node_value=''):
        self.node_type = node_type
        self.node_value = node_value
        self.parent = None
        self.right = None
        self.left = None

    def __str__(self):
        if self.left is None and self.right is None:
            return '%s (%s)' % (self.node_type, self.node_value)
        elif not self.node_type:
            return 'EMPTY'
        else:
            return '%s [l=%s,r=%s]' % (self.node_type, self.left, self.right)


    def __repr__(self):
        return self.__str__()

    def is_empty(self):
        return False if self.node_type else True

    '''
    Adds a node to the left of the current node
    '''
    def add_left(self, node):
        self.left = node
        node.parent = self
        return self.left

    '''
        Adds a node to the right of the current node
    '''
    def add_right(self, node):
        self.right = node
        node.parent = self
        return self.right



    '''
    sets the left or the right pointer of the
    parent node to none
    '''

    def nullify(self):
        if self.parent is None:
            pass
        # if the current node is on the left of the parent
        # we nullify it
        elif self.parent.left == self:
            self.parent.left = None
        else:
        # if the current node ison the right of the parent
        # we nullify it
            self.parent.right = None


        '''
        transplants children node to their parent
        '''
    def transplant_by_right(self):
        if self.right is None:
            return False

        # set the parent of the right child of the current node
        # to the parent
        self.right.parent = self.parent

        if self.parent is None:
            return False
        # if the current node is on the left of
        # its parent, set the pointer of the left
        # of its parent to the right of the current
        # node
        if self.parent.left == self:
            self.parent.left = self.right
        else:
            self.parent.right = self.right

        return True

    def transplant_by_left(self):
        if self.left is None:
            return False

        self.left.parent = self.parent

        if self.parent is None:
            return False

        if self.parent.left == self:
            self.parent.left = self.left
        else:
            self.parent.right = self.left

        return True


    def preorder_traverse(self):
        return self.__preorder_traverse(self)

    '''
    Preorder traversal of the tree
    '''
    def __preorder_traverse(self, node):
        if node.is_empty():
            return tuple()
        if node.left is None and node.right is None:
            return (node.node_type, node.node_value)
        else:
            return (node.node_type, node.__preorder_traverse(node.left), node.__preorder_traverse(node.right))
