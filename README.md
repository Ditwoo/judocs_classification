# Task

Using data from [lawinsider](https://www.lawinsider.com) (samples of contracts) need to create classifier which predict using sample paragraph (or major part of text) to which section of contract it belongs to.

So here is __TODO__ list:

1. Load data from [lawinsider](https://www.lawinsider.com).

  _Note. The're few types of files such as .docx and .pdf._

2. Parse data and mark headers, paragraphs, sections, subsections, lists (__only one level of subsections!__).

3. Create and train few models.

4. Get the F1 scores of each model on independent data.

5. Boost the scores!

# `parser.py`

Parse your folder with data and create in directory where was runed folder `parsed_data` which has 2 folders - `clean` and `parsed`.

Run example:

```bash
python3 parser.py <data folder> <size of data>
```

Or more concrete example:

```bash
python3 parser lawinsider_data 100
```

After runing this you will have in `clean` and `parsed` folders with __100__ parsed __.txt__ files in them.


# Links

* Data - [lawinsider.com/education](https://www.lawinsider.com/education)