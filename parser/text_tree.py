from parser.tag import Tag
from queue import Queue


class TextTree:
    # tree params
    parent = None
    subtrees = []
    # tree data
    tag = None
    left, right = 0, 0  # open and close tag positions

    def __init__(self, start_pos: int, end_pos: int, tag: Tag, parent=None):
        self.parent = parent
        self.subtrees = []
        # data
        self.tag = tag
        self.left = start_pos
        self.right = end_pos

    def __str__(self):
        return "<tag={},left={},right={},subtrees_size={}>".format(str(self.tag),
                                                                   self.left,
                                                                   self.right,
                                                                   len(self.subtrees))

    def __repr__(self):
        subtrees_text = ",".join(str(item.tag) for item in self.subtrees)
        repr_text = "<tag{},left={},right={},subtrees=[{}]>".format(str(self.tag),
                                                                    self.left, self.right,
                                                                    subtrees_text)
        return repr_text

    def tag_lines(self, tag: Tag) -> list:
        positions = []
        nodes = Queue()
        nodes.put(self)

        while not nodes.empty():
            node = nodes.get()
            if node.tag == tag:
                positions.append((node.left, node.right))
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
                                                       left=t.left,
                                                       right=t.right))

        def recursive(t):
            if not t or not isinstance(t, TextTree):
                return
            print_tag(t)
            for item in t.subtrees:
                TextTree.in_order(item)

        def non_recursive(t):
            if not tree or not isinstance(tree, TextTree):
                return

            nodes_queue = Queue()
            nodes_queue.put(tree)

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

    :param tags: list of tuples where each element has structure (1 or 0, 1 or 0, Tag)
    :return: TextTree object
    """

    tree = TextTree(0, len(tags), None)
    current = tree

    i, tags_size = 0, len(tags)
    while i < tags_size:
        is_opened, is_closed, curr_tag = tags[i]
        if curr_tag:
            # open tag
            if is_opened:
                tmp = TextTree(start_pos=i, end_pos=i, tag=curr_tag, parent=current)
                current.subtrees.append(tmp)
                current = tmp
            # close tag
            if is_closed:
                current.right = i
                current = current.parent
        i += 1
    return tree
