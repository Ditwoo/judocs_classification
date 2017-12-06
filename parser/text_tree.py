from parser.tag import Tag
from queue import Queue


class TextTree:
    # tree params
    parent = None
    subtrees = []
    # tree data
    tag, op_pos, cl_pos = None, 0, 0

    def __init__(self, start_pos: int, end_pos: int, tag: Tag, parent=None):
        self.parent = parent
        self.subtrees = []
        # data
        self.tag = tag
        self.op_pos = start_pos
        self.cl_pos = end_pos

    def __str__(self):
        return "<tag={},left={},right={},subtrees_size={}>".format(str(self.tag),
                                                                   self.op_pos,
                                                                   self.cl_pos,
                                                                   len(self.subtrees))

    def __repr__(self):
        subtrees_text = ",".join(str(item.tag) for item in self.subtrees)
        repr_text = "<tag{},left={},right={},subtrees=[{}]>".format(str(self.tag),
                                                                    self.op_pos, self.cl_pos,
                                                                    subtrees_text)
        return repr_text

    def tag_lines(self, tag: Tag) -> list:
        positions = []
        nodes = Queue()
        nodes.put(self)

        while not nodes.empty():
            node = nodes.get()
            if node.tag == tag:
                positions.append((node.op_pos, node.cl_pos))
            for item in node.subtrees:
                nodes.put(item)
        return positions

    @staticmethod
    def in_order(tree, *, is_recursive: bool=False):
        """
        Centralised bypassing the tree.

        :param tree: tree
        :param is_recursive: flag which will run recursive or non recursive implementation
        :return:
        """
        def print_tag(t: TextTree):
            current_tag = str(t.tag) if t.tag else "File"
            print("~> {tag} ({left} - {right})".format(tag=current_tag,
                                                       left=t.op_pos,
                                                       right=t.cl_pos))

        def recursive(t):
            if not t or not isinstance(t, TextTree):
                return
            print_tag(t)
            for item in t.subtrees:
                TextTree.in_order(item)

        def non_recursive(t):
            if not t or not isinstance(t, TextTree):
                return

            nodes_queue = Queue()
            nodes_queue.put(t)

            while not nodes_queue.empty():
                node = nodes_queue.get()
                print_tag(node)

                for item in node.subtrees:
                    nodes_queue.put(item)

        if is_recursive:
            recursive(tree)
        else:
            non_recursive(tree)


def build_tree(tags: list):
    """
    Building tree using list of tags.

    :param tags: list of tuples where each element is a tuple where first element - bit flag, second - Tag
    :return: TextTree object
    """
    
    tags_size = len(tags)
    tree = TextTree(0, tags_size, None)
    current = tree

    i = 0
    while i < tags_size:
        bit_flag, curr_tag = tags[i]
        if curr_tag:
            # open tag
            if bit_flag & (1 << 0):
                tmp = TextTree(start_pos=i, end_pos=i, tag=curr_tag, parent=current)
                current.subtrees.append(tmp)
                current = tmp
            # close tag
            if bit_flag & (1 << 1):
                current.cl_pos = i
                current = current.parent
        i += 1
    return tree
