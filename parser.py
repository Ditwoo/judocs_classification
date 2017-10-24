import os
import re
import sys
import queue
import docx2txt
import nltk.data
from bs4 import BeautifulSoup

# All data loaded from lawinsider.com
# contracts link: https://www.lawinsider.com/educations

# default params for execute
DATA_FOLDER, PARSED_DATA_FOLDER = '', 'parsed_data'
DATA_SIZE = 10
FILE_TYPES = ['.docx', '.txt']


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
        self.set_color(color)

    def op(self) -> str:
        return self.__color + '<' + self.__tag_name + '>' + self.__reset_color

    def cl(self) -> str:
        return self.__color + '</' + self.__tag_name + '>' + self.__reset_color

    def set_color(self, color: str):
        if color:
            self.__color = color
            self.__reset_color = '\033[0m'

    def disable_color(self):
        self.__color = ''
        self.__reset_color = ''

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
            self.enable_colors()

    def enable_colors(self):
        self.LIST.set_color('\033[92m\033[4m')  # green and underlined
        self.LIST_ITEM.set_color('\033[92m')  # green
        self.SECTION.set_color('\033[93m')  # yellow
        self.TITLE.set_color('\033[91m\033[1m')  # red and bold

    def disable_colors(self):
        self.LIST.disable_color()
        self.LIST_ITEM.disable_color()
        self.SECTION.disable_color()
        self.TITLE.disable_color()


TAGS = FileTags(enable_colors=False)


# MAGIC METHOD
def tag_positions(text: str) -> tuple:
    """
    Generate list of tags positions and lines which match these tags.

    :param text: str, which will used for searching tags
    :return: tuple of lists
    """

    text_lines = text.splitlines()

    TITLE = re.compile(r'^\ufeff?([\w ]+)[^.]?')
    EXHIBIT = re.compile(r'^\ufeff?Exhibit.+$')
    EMPTY_LINE = re.compile(r'^\s*$')
    SECTION = re.compile(r'^[A-Z][A-z ]+[^.]?$')
    LIST = re.compile(r'^\s*(\d+\.?\)?|\w+\.?\)|\(\w+\)|•).*$', re.VERBOSE)

    def same_types_of_list(first, second):
        f_type, s_type = '', ''

        if re.match(r'\d+\.?\)?', first):
            f_type = r'\d+\.?\)?'
        elif re.match(r'\w+\.?\)', first):
            f_type = r'\w+\.?\)'
        elif re.match(r'\(\w+\)', first):
            f_type = r'\(\w+\)'
        elif re.match(r'•', first):
            f_type = r'•'

        if re.match(r'\d+\.?\)?', second):
            s_type = r'\d+\.?\)?'
        elif re.match(r'\w+\.?\)', second):
            s_type = r'\w+\.?\)'
        elif re.match(r'\(\w+\)', second):
            s_type = r'\(\w+\)'
        elif re.match(r'•', second):
            s_type = r'•'

        return f_type == s_type and f_type != ''

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

    # try to search another tags after title position
    for i in range(title_pos, len(text_lines)):
        line = text_lines[i]
        # in case of empty line or line with whitespaces
        if len(line) == 0 or EMPTY_LINE.match(line):
            continue
        elif SECTION.match(line) and line.isupper():
            flags[i] = ('s', '')
        elif LIST.match(line):
            tmp = LIST.match(line).group(1)
            flags[i] = ('l', tmp)

    # remove mismatched sections inside of lists
    for i in range(1, len(flags) - 1):
        flag, item_type = flags[i]

        if flag == 's':
            # checking if marked 'i' as section between one list
            upper, lower = i - 1, i + 1
            while upper > 0:
                _, upper_type = flags[upper]
                while lower < len(flags):
                    _, lower_type = flags[lower]
                    if same_types_of_list(upper_type, lower_type):
                        flags[i] = ('', '')
                    lower += 1
                upper -= 1
    return flags, text_lines


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


# MAGIC METHOD
def parse_raw_text(text: str) -> str:
    """
    Parse text and add tags to it.

    :param text: string which need to be tagged
    :return: str with tags
    """

    text_tags, lines = tag_positions(text)
    i = 0
    is_opened_section = False
    while i < len(lines):
        tag, modifier = text_tags[i]

        if tag == 't':
            lines[i] = Tag.wrap(lines[i], FileTags.TITLE)
        elif tag == 'l':
            lines[i] = Tag.wrap(lines[i], FileTags.LIST)
        elif tag == 's':
            if is_opened_section:
                lines[i - 1] = lines[i - 1] + '\n' + FileTags.SECTION.cl()
            # open new section tag
            lines[i] = FileTags.SECTION.op() + '\n' + lines[i]
            is_opened_section = not is_opened_section

        # close section at the end of file
        if i + 1 == len(lines) and not is_opened_section:
            lines[i] = lines[i] + '\n' + FileTags.SECTION.cl()

        # increase counter
        i += 1

    return '\n'.join(lines)


def read_text(filename: str) -> str:
    """
    Read text from files with extensions .txt, .html or .docx.

    :param filename: string
    :return: string with readable text.
    """

    # getting cute text from .html
    if filename.endswith('.html'):
        # getting file content
        with open(filename, 'r', encoding='utf-8') as input_file:
            content = input_file.read()
        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text()

    elif filename.endswith('.docx'):
        text = docx2txt.process(filename)

    else:
        # getting file content
        with open(filename, 'r', encoding='utf-8') as input_file:
            content = input_file.read()
        text = content
    return text


def get_files_in_folder(data_folder: str,
                        file_extensions: list,
                        count_of_files: int = -1) -> list:
    """
    Get all files with extensions from folder(and all subfolders).

    :param data_folder: str, path to folder
    :param file_extensions: list of strings
    :param count_of_files: int, max size of output list of files, in case -1 return all files
    :return: list of files which have specific extensions
    """
    # check for existing folder 
    if not os.path.isdir(data_folder):
        raise FileNotFoundError

    def is_valid_file(extensions, filename):
        """
        Checks does filename matches extensions.
        """
        for f_ext in extensions:
            if filename.endswith(f_ext):
                return True
        return False

    subfolders = queue.Queue()
    subfolders.put(data_folder)
    files = []
    while not subfolders.empty():
        curr_folder = subfolders.get()
        for f in os.listdir(curr_folder):
            full_f = os.path.join(curr_folder, f)
            # case f is folder
            if os.path.isdir(full_f):
                subfolders.put(full_f)
            # case f is some file
            if is_valid_file(file_extensions, f):
                files.append(full_f)
            # checks if files list is overfilled
            if count_of_files:
                if len(files) == count_of_files:
                    return files
    return files


def main(*args):
    def print_faq():
        print('\nScript usage:')
        print('\t<script name> <data folder> <count of files>\n')
        print('Example')
        print('python3 parser.py data\n')

    def parse_one_file(filename, *, to_file=''):
        global TAGS
        # parsing file
        text = read_text(filename)
        parsed_text = parse_raw_text(text)
        if to_file:
            # saving to file

            with open(to_file, 'w', encoding='utf-8') as out_file:
                out_file.write(parsed_text)
        else:
            print(parsed_text)

    def parse_folder(foldername, filetypes, size, output_folder):
        paths_to_data_files = get_files_in_folder(foldername, filetypes, size)

        # check for existing parsed data folder
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # create folder for clean texts
        output_clean = os.path.join(output_folder, 'clean')
        if not os.path.exists(output_clean):
            os.makedirs(output_clean)

        # create folder for parsed texts
        output_parsed = os.path.join(output_folder, 'parsed')
        if not os.path.exists(output_parsed):
            os.makedirs(output_parsed)

        # parsing files
        print('Parsing {} files from \'{}\' to \'{}\':'.format(size if size > 0 else 'all',
                                                               foldername,
                                                               output_folder))
        for path_to_file in paths_to_data_files:
            print('  [*]', path_to_file.rsplit('/', 1)[1])

            # remove path from file
            _, filename = path_to_file.rsplit('/', 1)
            # remove extension (for example '.html' or '.docx')
            filename, _ = filename.split('.', 1)
            filename += '.txt'
            try:
                # working with clean file
                path_to_clean = os.path.join(output_clean, filename)
                clean_text = read_text(path_to_file)
                # saving clean file
                with open(path_to_clean, 'w', encoding='utf-8') as out_file:
                    out_file.write(clean_text)

                # working with parsed file
                path_to_parsed = os.path.join(output_parsed, filename)
                parse_one_file(path_to_clean, to_file=path_to_parsed)
            except Exception as e:
                print('[!]', e)
                continue

    global DATA_FOLDER
    global DATA_SIZE
    global PARSED_DATA_FOLDER
    # case call <script>
    if len(args) == 1:
        print_faq()
    # case call <script> <file or folder>
    elif len(args) == 2:
        target = args[1]
        # case
        if os.path.isdir(target):
            DATA_FOLDER, PARSED_DATA_FOLDER = target, os.path.join(target, PARSED_DATA_FOLDER)
            DATA_SIZE = -1  # parse all file in folder
            parse_folder(DATA_FOLDER, FILE_TYPES, DATA_SIZE, PARSED_DATA_FOLDER)
        else:
            parse_one_file(filename=args[1])
    # case call <script> <data folder> <count of files>
    elif len(args) == 3:
        DATA_FOLDER, DATA_SIZE = args[1], int(args[2])
        parse_folder(DATA_FOLDER, FILE_TYPES, DATA_SIZE, PARSED_DATA_FOLDER)


if __name__ == '__main__':
    main(*sys.argv)
