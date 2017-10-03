import os
import re
import sys
import nltk.data
from bs4 import BeautifulSoup

# All data loaded from lawinsider.com
# contracts link: https://www.lawinsider.com/education
# this unpacked folder need to pass to DATA_FOLDER

# default params for execute
DATA_FOLDER = ''
PARSED_DATA_FOLDER = 'parsed_data'
DATA_SIZE = 10
FILE_TYPES = ['.html']


class TitlePatterns:
    exhibit_title = re.compile(r'^Exhibit\s\d+.\d+', re.M)
    # first group will be title
    upper_case_titles = re.compile(r'([A-Z ]+)\n', re.M)
    numbered_title = re.compile(r'\d+\.?\s+', re.M)
    # <number>.<white spaces>[A-Z][<not end of sentence char>][<end of sentence char>]
    numbered_title_with_first_sentence = re.compile(r'\d+\.\s+([A-Z][^\.!?]*[\.!?])', re.M)


class SectionPatterns:
    # first group will be title
    captioned_section_with_some_text = re.compile(r'^(SECTION\s.+)', re.M)  # SECTION <some text>


class ListPatterns:
    # this lists probably can be sections
    # first group will contain number
    num_with_point = re.compile(r'^\s*?(\d+\.).', re.M)  # <number>.
    num_with_bracket = re.compile(r'^\s*?(\d+\))', re.M)  # <number>)
    char_with_point = re.compile(r'^\s*?([A-Z]+\.)', re.M)  # <char>.
    char_with_bracket = re.compile(r'^\s*?([A-Z]+\.)', re.M)  # <char>)


class SubListPatterns:
    bracketed_list = re.compile(r'\([A-z\d]+\)', re.M)  # (<number or chars>)
    # first group of list_with_points will contain number
    list_with_points = re.compile(r'\s(\d+\.[\d+\.+]+)', re.M)  # <number>. ... .<number>


class Tag:
    __color = ''
    __reset_color = ''

    def __init__(self, name: str, color: str=''):
        # Expected that color will be something like this:
        # \033[92m      (green)
        # \033[91m      (red)
        # \033[93m      (yellow)
        # \033[4m       (underlined)
        # \033[1m       (bold)
        self.__tag_name = name
        self.__color = color

    def op(self) -> str:
        return self.__color + '<' + self.__tag_name + '>' + self.__reset_color

    def cl(self) -> str:
        return self.__color + '</' + self.__tag_name + '>' + self.__reset_color

    def set_color(self, color: str):
        self.__color = color
        self.__reset_color = '\033[0m'
    
    @staticmethod
    def wrap(text: str, tag) -> str:
        return tag.op() + text + tag.cl()


class FileTags:
    LIST = Tag('list')
    LIST_ITEM = Tag('list item')
    SECTION = Tag('section')
    TITLE = Tag('title')
    
    def __init__(self, *, enable_colors=False):
        if enable_colors:
            self.LIST.set_color('\033[92m\033[4m')  # green and underlined
            self.LIST_ITEM.set_color('\033[92m')  # green
            self.SECTION.set_color('\033[93m')  # yellow
            self.TITLE.set_color('\033[91m\033[1m')  # red and bold


TAGS = FileTags(enable_colors=False)


# TODO: very naive to suppose that end of text is the end of last section
def section_positions(text: str) -> list:
    positions = []
    pattern = None

    if SectionPatterns.captioned_section_with_some_text.search(text):
        # SECTION <some text>
        pattern = SectionPatterns.captioned_section_with_some_text
    elif TitlePatterns.upper_case_titles.search(text):
        # UPPERCASE TITLES
        pattern = TitlePatterns.upper_case_titles
    elif ListPatterns.num_with_point.search(text):
        # <number>. <text>
        pattern = ListPatterns.num_with_point
    elif ListPatterns.num_with_bracket.search(text):
        # <number>) <text>
        pattern = ListPatterns.num_with_bracket
    else:
        return positions

    match_pos = [item.start(1) for item in pattern.finditer(text)]
    match_pos.append(len(text) - 1)  # suppose that last section ends when ends file

    positions = list(zip(match_pos[:-1], match_pos[1:]))
    #  The same as lower line:
    #  positions = [(match_pos[i], match_pos[i + 1]) for i in range(len(match_pos) - 1)]
    return positions


# TODO: fix problem of list endings
def list_positions(section_text: str) -> list:
    positions = []
    pattern = None

    if ListPatterns.num_with_point.search(section_text):
        # <number>. <text>
        pattern = ListPatterns.num_with_point
    elif ListPatterns.num_with_bracket.search(section_text):
        # <number>) <text>
        pattern = ListPatterns.num_with_bracket
    elif ListPatterns.char_with_point.search(section_text):
        # <char>. <text>
        pattern = ListPatterns.char_with_point
    elif ListPatterns.char_with_bracket.search(section_text):
        # <char>) <text>
        pattern = ListPatterns.char_with_bracket
    else:
        return positions

    match_pos = [item.start(1) for item in pattern.finditer(section_text)]
    # get position of last index start
    last_list_item_pos = match_pos[-1]
    # get subtext from previous position
    subtext = section_text[last_list_item_pos:]
    # suppose that first paragraph is the end of list
    first_paragraph_in_list_item = subtext.split('\n\n')[0]
    # add end of list
    match_pos.append(last_list_item_pos + len(first_paragraph_in_list_item))

    positions = list(zip(match_pos[:-1], match_pos[1:]))
    return positions


def has_exhibit(text: str) -> bool:
    return True if TitlePatterns.exhibit_title.search(text) else False


# TODO: add more flexible way of searching titles
def tag_positions(text: str) -> list:
    def get_title_pos(some_text: str) -> tuple:
        """
        Get start and end positions of text title

        :param some_text: string
        :return: begin and end positions of title
        """
        # working with files which has Exhibit at top
        if has_exhibit(some_text):
            # suppose that first not empty line after exhibit is title
            return TitlePatterns.upper_case_titles.search(some_text).span(1)
        return 0, 0

    def get_list_positions(some_text: str) -> list:
        """
        Get list of positions of list elements in text with tags

        :param some_text: string
        :return: list of tuples where elements has structure (<index>, <tag>)
        """
        unwrapped_pos = []
        list_pos = list_positions(some_text)
        if list_pos:
            for start, end in list_pos:
                # remember opening and closing positions of list
                unwrapped_pos.append((start, TAGS.LIST.op()))
                unwrapped_pos.append((end, TAGS.LIST.cl()))
        return unwrapped_pos

    def get_sections_positions(some_text: str) -> list:
        """
        Get list of positions sections with lists in text with proper tag

        :param some_text: string
        :return: list of tuples where elements has structure (<index>, <tag>)
        """
        unwrapped_pos = []
        section_pos = section_positions(some_text)
        if section_pos:
            for start, end in section_pos:
                # remember opening positions of list
                unwrapped_pos.append((start, TAGS.SECTION.op()))
                # search for list in section
                list_pos = get_list_positions(some_text[start:end])
                if list_pos:
                    list_pos = [(pos + start, tag) for pos, tag in list_pos]
                unwrapped_pos.extend(list_pos)
                # remember closing position of list
                unwrapped_pos.append((end, TAGS.SECTION.cl()))
        return unwrapped_pos

    positions = []
    title_start, title_end = get_title_pos(text)
    if title_end:
        # remember opening and closing positions of title
        positions.append((title_start, TAGS.TITLE.op()))
        positions.append((title_end, TAGS.TITLE.cl()))

    text_without_title = text[title_end:] if title_end else text
    sl_pos = get_sections_positions(text_without_title)
    sl_pos = [(pos + title_end, tag)for pos, tag in sl_pos]

    positions.extend(sl_pos)

    # # get positions of sections
    # sect_positions = section_positions(text)
    # for s_start, s_end in sect_positions:
    #     # remember opening position of section
    #     positions.append((s_start, TAGS.SECTION.op()))
    #     # get section substring and parse it
    #     lst_positions = list_positions(text[s_start:s_end])
    #     if lst_positions:
    #         for l_start, l_end in lst_positions:
    #             # remember opening position of list
    #             positions.append((l_start + s_start, TAGS.LIST.op()))
    #             # remember closing position of list
    #             positions.append((l_end + s_start, TAGS.LIST.cl()))
    #     # remember closing position of section
    #     positions.append((s_end, TAGS.SECTION.cl()))
    return positions


def tokenize_onto_sentences(text: str) -> list:
    """
    Split text (only english) to sentences using nltk.

    :param text: string
    :return: list of strings where each string is one sentence
    """
    # load english dictionary if need
    if not nltk.data.find('tokenizers/punkt/english.pickle'):
        nltk.download('punkt')
    tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
    # tokenize into sentences
    sentences = tokenizer.tokenize(text)
    return sentences


# DEPRECATED
def tokenize_onto_paragraphs(text: str) -> list:
    """
    WARNING this method is deprecated!
    Split text onto paragraphs and add tags to this paragraphs if can.

    :param text: string
    :return: list of strings
    """
    # text constants
    PARAGRAPH_PATTERN = re.compile(r'\s*?\n\s*?\n\s*?')
    SECTION_PATTERN = re.compile(r'\d+\.?.*\.')
    SUBLIST_PATTERN = re.compile(r'^\s?(\d+.\d+?\)?|\(.*\)).*')

    # working with paragraphs
    raw_paragraphs = [
        item for item in re.split(
            PARAGRAPH_PATTERN,
            text) if item]
    paragraphs = []
    # merging lists into sections
    is_ended_list = True
    for item in raw_paragraphs:
        if SUBLIST_PATTERN.match(item):
            if is_ended_list:
                paragraphs[-1] += '\n' + TAGS.LIST.op()
                is_ended_list = False
            paragraphs[-1] += '\n' + Tag.wrap(item, TAGS.LIST_ITEM)
            continue
        else:
            if len(paragraphs) and paragraphs[-1].endswith(TAGS.LIST_ITEM.cl()):
                paragraphs[-1] += '\n' + TAGS.LIST.cl() + '\n'
            is_ended_list = True
        paragraphs.append(item)

    return paragraphs


def parse_raw_text(text: str) -> str:
    """
    Parse text and add tags to it.

    :param text: string which need to be tagged
    :return: str with tags
    """

    text_tags = tag_positions(text)
    tt_pos = 0
    tagged_text = ''

    for i in range(len(text)):
        while tt_pos < len(text_tags) and i == text_tags[tt_pos][0]:
            if text_tags[tt_pos][0] == text_tags[tt_pos - 1][0]:
                tagged_text += text_tags[tt_pos][1] + '\n'
            else:
                tagged_text += '\n' + text_tags[tt_pos][1] + '\n'
            tt_pos += 1
        tagged_text += text[i]

    return tagged_text


def read_text(filename: str) -> str:
    """
    Read text from .txt or .html
    :param filename: string
    :return: string with readable text.
    """
    content = ''
    text = ''
    # getting file content
    with open(filename, 'r', encoding='utf-8') as input_file:
        content = input_file.read()
    # geting cute text from .html
    if filename.endswith('.html'):
        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text()
    else:
        text = content
    return text


def parse_file(filename: str) -> tuple:
    """
    Parsing existing file.
    """
    raw_text = read_text(filename)
    # invoke parser
    marked_text = parse_raw_text(raw_text)
    return raw_text, marked_text


def get_path_to_data_files(data_folder: str,
                           file_endings: list,
                           max_list_size: int) -> list:
    # Parsing data folder which has structure like:
    #
    #       <data-folder>/
    #         <upper-folder>/
    #             <middle-folder_>/
    #                 some-file.html
    #                 some-file.json
    #                 ...
    #             ...
    #         ...
    #
    files_list = []
    for file_in_data in os.listdir(data_folder):
        # parsing upper folders
        upper_folder = os.path.join(data_folder, file_in_data)
        if os.path.isdir(upper_folder):
            for file_in_upper in os.listdir(upper_folder):
                # parsing middle folders
                middle_folder = os.path.join(upper_folder, file_in_upper)
                if os.path.isdir(middle_folder):
                    for filename in os.listdir(middle_folder):
                        # looking for acceptable files
                        for file_ending in file_endings:
                            if filename.endswith(file_ending) and len(
                                    files_list) < max_list_size:
                                path_to_file = os.path.join(
                                    middle_folder, filename)
                                files_list.append(path_to_file)
    return files_list


def main(*args):
    global DATA_FOLDER
    global DATA_SIZE
    # case call <script>
    if len(args) == 1:
        print('\nScript usage:')
        print('\t<script name> <data folder> <count of files>\n')
        print('Example')
        print('python3 parser.py data\n')
    # case call <script> <data folder> <count of files>
    if len(args) == 3:
        DATA_FOLDER = args[1]
        DATA_SIZE = int(args[2])

        paths_to_data_files = get_path_to_data_files(data_folder=DATA_FOLDER,
                                                     file_endings=FILE_TYPES,
                                                     max_list_size=DATA_SIZE)

        # check for existing parsed data folder
        if not os.path.exists(PARSED_DATA_FOLDER):
            os.makedirs(PARSED_DATA_FOLDER)
        # create folder for clean texts
        CLEAN_FOLDER = os.path.join(PARSED_DATA_FOLDER, 'clean')
        if not os.path.exists(CLEAN_FOLDER):
            os.makedirs(CLEAN_FOLDER)
        # create folder for parsed texts
        PARSED_FOLDER = os.path.join(PARSED_DATA_FOLDER, 'parsed')
        if not os.path.exists(PARSED_FOLDER):
            os.makedirs(PARSED_FOLDER)

        # parsing files
        print('Parsing {} files from {} :'.format(DATA_SIZE, DATA_FOLDER))
        for filepath in paths_to_data_files:
            print('  [*]', filepath.rsplit('/', 1)[1])
            try:
                clean_text, parsed_text = parse_file(filepath)
            except Exception as e:
                print('[!]', e)
                continue

            # remove path to file
            _, fname = filepath.rsplit('/', 1)
            # remove .html
            fname, _ = fname.split('.', 1)
            fname += '.txt'
            # saving files to folders
            with open(os.path.join(CLEAN_FOLDER, fname), 'w') as out_file:
                out_file.write(clean_text)
            with open(os.path.join(PARSED_FOLDER, fname), 'w') as out_file:
                out_file.write(parsed_text)


if __name__ == '__main__':
    main(*sys.argv)
