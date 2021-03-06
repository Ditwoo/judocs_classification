
class TerminalTextFlags:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Tag:
    __color = ''
    __reset_color = ''

    def __init__(self, name: str, color: str=''):
        self.__tag_name = name
        self.set_color(color)

    def op(self) -> str:
        return "{}<{}>{}".format(self.__color,
                                 self.__tag_name,
                                 self.__reset_color)

    def cl(self) -> str:
        return "{}</{}>{}".format(self.__color,
                                  self.__tag_name,
                                  self.__reset_color)

    def set_color(self, color: str):
        if color:
            self.__color = color
            self.__reset_color = '\033[0m'

    def disable_color(self):
        self.__color = ''
        self.__reset_color = ''

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__tag_name == other.__tag_name
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return '<' + self.__tag_name + '>'

    def __repr__(self):
        return '<' + self.__tag_name + '>'

    @staticmethod
    def wrap(text: str, tag) -> str:
        return tag.op() + text + tag.cl()


class FileTags:
    LIST = Tag('l')
    LIST_ITEM = Tag('le')
    SECTION = Tag('s')
    TITLE = Tag('title')
    PLAIN_TEXT = Tag('p')

    def __init__(self, *, enable_colors=False):
        if enable_colors:
            self.enable_colors()

    def enable_colors(self):
        self.LIST.set_color(TerminalTextFlags.OKGREEN + TerminalTextFlags.UNDERLINE)
        self.LIST_ITEM.set_color(TerminalTextFlags.OKGREEN)
        self.SECTION.set_color(TerminalTextFlags.WARNING)
        self.TITLE.set_color(TerminalTextFlags.FAIL + TerminalTextFlags.BOLD)
        self.PLAIN_TEXT.set_color(TerminalTextFlags.OKBLUE)

    def disable_colors(self):
        self.LIST.disable_color()
        self.LIST_ITEM.disable_color()
        self.SECTION.disable_color()
        self.TITLE.disable_color()
        self.PLAIN_TEXT.disable_color()
