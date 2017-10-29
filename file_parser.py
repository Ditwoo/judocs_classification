import os
import sys
import queue
import docx2txt
from bs4 import BeautifulSoup

from parser import FileTags, parse_raw_text

# All data loaded from lawinsider.com
# contracts link: https://www.lawinsider.com/educations


# default params for execute
DATA_FOLDER, PARSED_DATA_FOLDER = '', 'parsed_data'
DATA_SIZE = 10
FILE_TYPES = ['.docx', '.txt']
TAGS = FileTags(enable_colors=False)


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
        print('python3 core.py data\n')

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
        print('Parsing {} files from \'{}\' to \'{}\':'.format(
            size if size > 0 else 'all', foldername, output_folder))
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
            DATA_FOLDER, PARSED_DATA_FOLDER = target, os.path.join(
                target, PARSED_DATA_FOLDER)
            DATA_SIZE = -1  # parse all file in folder
            parse_folder(
                DATA_FOLDER,
                FILE_TYPES,
                DATA_SIZE,
                PARSED_DATA_FOLDER)
        else:
            parse_one_file(filename=args[1])
    # case call <script> <data folder> <count of files>
    elif len(args) == 3:
        DATA_FOLDER, PARSED_DATA_FOLDER = args[1], os.path.join(
            args[1], PARSED_DATA_FOLDER)
        DATA_SIZE = int(args[2])
        parse_folder(DATA_FOLDER, FILE_TYPES, DATA_SIZE, PARSED_DATA_FOLDER)


if __name__ == '__main__':
    main(*sys.argv)
