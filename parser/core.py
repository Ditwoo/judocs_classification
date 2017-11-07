import re
from parser.tag import FileTags
from parser.text_tree import TextTree, build_tree


TITLE = re.compile(r"""^                       # beginning of the string  
                       \ufeff?                 # optional char
                       ([\w ]+)                # words with spaces
                       [^.]?                   # without . at the end
                       """, re.VERBOSE)
EXHIBIT = re.compile(r"""^                     # beginning of the string
                         \ufeff?               # optional char
                         Exhibit               # text which indicates us that next nonemty line will be title
                         .+$                   # some chars till the end of string
                         """, re.VERBOSE)
EMPTY_LINE = re.compile(r'^\s*$')
EXACT_SECTION = re.compile(r"""^
                               (Section.*|
                               [A-Z ]+|
                               \d+\.\s*[A-Z ]+)
                               $""", re.VERBOSE)
SECTION = re.compile(r"""^                     # beginning of the string
                         [A-Z]                 # uppercase letter
                         [a-z ]+               # some letters
                         [^.]?$                # without . at the end
                         """, re.VERBOSE)
LIST = re.compile(r"""^                        # beginning of the string
                      \s*                      # whitespaces
                      (\d+(\.|\))|             # <num> or <num>. or <num>)
                      \w(\.|\))|               # <char> or <char>. or <char>) 
                      \(\w+\)|                 # (<chars>)
                      (•|-|\*))                # • or - or *
                      .*$                      # some text till the end
                      """, re.VERBOSE)
SINGLE_NUMBER = re.compile(r"""^               # beginning of the string
                                \s*            # whitespaces
                                [\d\.\)]+      # number
                                \s*            # whitespaces
                                $""", re.VERBOSE)

LIST_TYPES = [r'(\d+)\.?\)?',  # number
              r'(\w+)\.?\)',   # chars
              r'\((\w+)\)',    # chars
              r'(•|-|\*)']     # special symbol


def _list_type(list_string: str):
    for list_pattern in LIST_TYPES:
        if re.match(list_pattern, list_string):
            return list_pattern


def _is_start_of_list(list_string: str):
    list_type = _list_type(list_string)
    if list_type == LIST_TYPES[0]:
        return _list_content(list_string) == '1'
    elif list_type == LIST_TYPES[1] or list_type == LIST_TYPES[2]:
        return _list_content(list_type) in 'Aai'
    elif list_type == LIST_TYPES[3]:
        return True
    else:
        return False


def _list_content(list_string: str):
    """
    Return chean number (as string) or text of list
    :param list_string:
    :return:
    """
    output = ''
    for list_pattern in LIST_TYPES:
        if re.match(list_pattern, list_string):
            return re.match(list_pattern, list_string).group(1)
    return output


def _is_same_types_of_list(first: str, second: str):
    """
    Checks that two strings has same list structure.

    :param first: string
    :param second: string
    :return: True or False
    """

    f_type, s_type = _list_type(first), _list_type(second)
    return f_type != '' and f_type == s_type


def _is_cmp(first: str, second: str, cmp=lambda x, y: x > y) -> bool:
    ftype, stype = _list_type(first), _list_type(second)
    if ftype == stype and ftype != '':
        fcontent, scontent = _list_content(first), _list_content(second)
        if ftype == LIST_TYPES[0]:  # number
            return cmp(int(fcontent), int(scontent))
        else:
            return cmp(fcontent, scontent)
    return False


def _is_growth(first: str, second: str):
    ftype, stype = _list_type(first), _list_type(second)
    if ftype == stype and ftype != '':
        fcontent, scontent = _list_content(first), _list_content(second)
        if ftype == LIST_TYPES[0]:  # number
            return int(scontent) - int(fcontent) == 1
        elif ftype == LIST_TYPES[1] or ftype == LIST_TYPES[2]:
            return fcontent < scontent
        else:
            return fcontent == scontent


def _get_list_sequence(flags: list, lines: list):
    list_pos = [i for i in range(len(lines)) if flags[i][0] == 'l']
    list_repr = [LIST.match(lines[pos]).group(1) for pos in list_pos]

    list_stack = []

    i, len_pos = 0, len(list_pos)
    while i < len_pos:
        j, lst = i + 1, []
        while j < len_pos and _is_growth(list_repr[i], list_repr[j]):
            lst.append(list_pos[i])
            i += 1
            j += 1

        if len(lst):
            list_stack.append(lst)

        lst = []
        while j < len_pos and _is_cmp(list_repr[i], list_repr[j]):
            i += 1
            j += 1

        if len(lst):
            list_stack.append(lst)

        i += 1

    return list_stack


def _normalize_lines(text_lines: list) -> list:
    i, lines_size = 1, len(text_lines)
    normalized = [text_lines[0]]

    while i < lines_size:
        line = text_lines[i]
        # continue previous sentence
        if re.match(r'\s*^[a-z]+', line):
            while len(normalized) > 0 and EMPTY_LINE.match(normalized[-1]):
                normalized.pop()
            normalized[-1] += line
        else:
            if not EMPTY_LINE.match(normalized[-1]) and not EMPTY_LINE.match(line):
                normalized.append(line)

        i += 1

    return normalized


# MAGIC METHOD
def tag_positions(text: str) -> tuple:
    """
    Generate list of tags positions and lines which match these tags.

    :param text: str, which will used for searching tags
    :return: tuple of lists
    """

    text_lines = _normalize_lines(text.splitlines())
    lines_length = len(text_lines)
    # first - type of tag, second - tag info
    flags = [('', '') for _ in text_lines]
    title_pos = 0

    # check that file has 'Exhibit' line
    if EXHIBIT.match(text_lines[title_pos]):
        title_pos += 1
        while EMPTY_LINE.match(text_lines[title_pos]):
            title_pos += 1
        flags[title_pos] = ('t', '')
        title_pos += 1
    # check that first line of file has title
    elif TITLE.match(text_lines[title_pos]):
        flags[title_pos] = ('t', '')
        title_pos += 1

    # searching another tags
    for i in range(title_pos, lines_length):
        line = text_lines[i]
        # in case of empty line or line with whitespaces
        if EMPTY_LINE.match(line):
            continue
        elif SECTION.match(line) or EXACT_SECTION.match(line):
            flags[i] = ('s', '')
            continue
        elif LIST.match(line) and not SINGLE_NUMBER.match(line):
            tmp = LIST.match(line).group(1)
            flags[i] = ('l', tmp)

    # for i in range(1, lines_length - 1):
    #     flag, item_type = flags[i]
    #     # remove mismatched sections inside of lists
    #     if flag == 's':
    #         # checking if marked 'i' as section between one list
    #         upper, lower = i - 1, i + 1
    #         while upper > 0:
    #             _, upper_type = flags[upper]
    #             while lower < len(flags):
    #                 _, lower_type = flags[lower]
    #                 if _is_same_types_of_list(upper_type, lower_type):
    #                     flags[i] = ('', '')
    #                 lower += 1
    #             upper -= 1

    # checking that right matched sections
    def is_all_sections_uppercase(tags, lines):
        """
        Check that all text which matched as section is uppercase.

        :param tags: list of tuples
        :param lines: list of text strings
        :return: True if all sections is uppercase and False otherwise.
        """
        all_sections_uppercase = True
        for i in range(len(lines)):
            if tags[i][0] != 's':
                continue
            if not lines[i].isupper():
                all_sections_uppercase = False
                break
        return all_sections_uppercase

    if not is_all_sections_uppercase(flags, text_lines):
        for i in range(title_pos, lines_length):
            tag, info = flags[i]
            line = text_lines[i]
            if tag == 's' and line.isupper():
                flags[i] = ('', '')

    for i in range(lines_length):
        line = text_lines[i]
        if len(line) == 0 or EMPTY_LINE.match(line) or flags[i][0] != '':
            continue
        else:
            flags[i] = ('p', '')

    def prettify_tags(tags: list):
        """
        Generate list of tuples where each element has structure of tuple where:

        - first element is number where first bit (0 indexed) indicates that opened tag
          and second bit indicates that closed tag
        - second element is tag (Tag object)

        :param tags: list of rude parsed tags.
        :return:
        """

        # list of tuples, where each element has structure - (<bit flags>, <tag>)
        pretty = [(0, '') for _ in tags]
        tag_pos, tags_size = 0, len(tags)
        is_opened_section, any_section = False, False
        while tag_pos < tags_size:
            tag, modifier = tags[tag_pos]
            if tag == 't':
                # set open tag bit and close tag bit
                bit_flags = (1 << 0) | (1 << 1)
                pretty[tag_pos] = (bit_flags, FileTags.TITLE)
            elif tag == 'l':
                # set open tag bit and close tag bit
                bit_flags = (1 << 0) | (1 << 1)
                pretty[tag_pos] = (bit_flags, FileTags.LIST)
            elif tag == 's':
                if is_opened_section:
                    # close tag
                    flag, tag = pretty[tag_pos - 1]
                    if tag == FileTags.SECTION:
                        pretty[tag_pos - 1] = flag | (1 << 1), tag
                # open tag
                pretty[tag_pos] = ((1 << 0), FileTags.SECTION)
                is_opened_section = not is_opened_section
                any_section = True
            elif tag == 'p':
                # set open tag bit and close tag bit
                bit_flags = (1 << 0) | (1 << 1)
                pretty[tag_pos] = (bit_flags, FileTags.PLAIN_TEXT)
            # case not closed section
            if tag_pos + 1 == tags_size and any_section and not is_opened_section:
                pretty[tag_pos] = ((1 << 1), FileTags.SECTION)
            tag_pos += 1
        return pretty

    return prettify_tags(flags), text_lines


def generate_tree(text: str) -> TextTree:
    """
    Generate text tree with tags.

    :param text: string which need to be tagged
    :return: TextTree object
    """
    text_tags, lines = tag_positions(text)
    return build_tree(text_tags)


# MAGIC METHOD
def parse_raw_text(text: str) -> str:
    """
    Parse text and add tags to it.

    :param text: string which need to be tagged
    :return: str with tags
    """

    text_tags, lines = tag_positions(text)

    i, lines_size = 0, len(lines)
    while i < lines_size:
        bit_flags, tag = text_tags[i]
        if tag:
            # opened tag
            if bit_flags & (1 << 0):
                lines[i] = tag.op() + ' ' + lines[i]
            # closed tag
            if bit_flags & (1 << 1):
                lines[i] = lines[i].rstrip() + ' ' + tag.cl()
        i += 1

    # TODO: remove lines without text
    return '\n'.join(lines)
