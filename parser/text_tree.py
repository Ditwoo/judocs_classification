from parser.tag import Tag


class TextTree:
    # tree params
    parent = None
    subtrees = []
    # tree data
    tag = None
    left, right = 0, 0  # open and close tag positions

    def __init__(self, start_pos: int, end_pos: int, tag: Tag, subtrees: list=[], parent=None):
        self.parent = parent
        self.subtrees = subtrees
        # data
        self.tag = tag
        self.left = start_pos
        self.right = end_pos

    def __str__(self):
        return "<tag={},left={},right={},subtrees_size={}>".format(str(self.tag),
                                                                   self.left,
                                                                   self.right,
                                                                   len(self.subtrees))

    def get_tags(self):
        pass

    @staticmethod
    def in_order(tree):
        if not tree or not isinstance(tree, TextTree):
            return

        current_tag = str(tree.tag) if tree.tag else "File"
        print("~> {tag} ({left} - {right})".format(tag=current_tag,
                                                   left=tree.left,
                                                   right=tree.right))
        for item in tree.subtrees:
            TextTree.in_order(item)


def build_tree(tags: list):
    tree = TextTree(0, len(tags), None)
    current = tree

    i, tags_size = 0, len(tags)
    while i < tags_size:
        is_opened, is_closed, curr_tag = tags[i]
        if curr_tag:
            # open tag
            if is_opened:
                tmp = TextTree(start_pos=i, end_pos=i, tag=curr_tag, subtrees=[], parent=current)
                current.subtrees.append(tmp)
                current = tmp
            # close tag
            if is_closed:
                current.right = i
                current = current.parent
        i += 1
    return tree


