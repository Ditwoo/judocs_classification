# Task

Using data from [lawinsider](https://www.lawinsider.com) (samples of contracts) need to create classifier which predict using sample paragraph (or major part of text) to which section of contract it belongs to.

So here is __TODO__ list:

1. Load data from [lawinsider](https://www.lawinsider.com).

  _Note. The're few types of files such as .docx and .pdf._

2. Parse data and mark headers, paragraphs, sections, subsections, lists (__only one level of subsections!__).

3. Create and train few models.

4. Get the F1 scores of each model on independent data.

5. Boost the scores!

# `file_parser.py`

Parse your folder with data and create in this folder (folder with your data) new directory `parsed_data` with  __.txt__ which will store text with tags.

Example:

```bash
python3 file_parser.py --folder <data folder> --output <output folder>
```

`file_parser.py` paramenters:

- `--folder` -- folder which will be parsed;

- `--size` -- (__optional__) total amount of files in folder which will be parsed;

- `--output` -- folder where will be stored tagged data;

- `--file` -- (__optional__) file which will be parsed and parsing content will be printed to stdout;

- `--color` -- (__optional__) enables color output to stdout;

NOTE: there is no conflicts between paramenters `--file` and `--folder`


# Links

* Data - [lawinsider.com/education](https://www.lawinsider.com/education)