
import os
import re
import pandas as pd
from pdfminer.high_level import extract_text

def extract_marketing_book(path='/Users/giovanni/OneDrive/_Progetti/_WE-COLLAB/PR2/materials', in_name='Marketing_book.xlsx', out_name='book.xlsx'):
    in_path = os.path.join(path, in_name)
    out_path = os.path.join(path, out_name)
    # read Marketing_book.xlsx as a Panda dataframe
    excel_data = pd.read_excel(in_path)
    data = pd.DataFrame(excel_data, columns=['Chapter', 'Subchapter', 'Text'])
    # for each row in xslx read the 3 columns and
    for index, row in data.iterrows():
        # copy the text (3rd column) to text_1
        text_1 = row['Text']
        # compute name of PDF file for that section
        chapter_name = row['Chapter']
        chapter = chapter_name.split()[0][:-1]
        section_name = '{}-{} {}.pdf'.format(chapter, index+1, row['Subchapter'])
        section_path = os.path.join(path, section_name)
        print(section_path)
        text_2 = extract_text(section_path)
        text = fix_diacritics(text_2)
        text = clear_section_text(text)
        # write to CSV file a row with updated text column
        row['Text'] = text
   # write to the CSV file the dataframe with updated sections' text
    data.to_excel(out_path)

# see: https://www.jlg-utilities.com/documentation_1_1/alphabets/Croatian.html
diacritics_map = {
    '~': 'č',
    '^': 'Č',
    '}': 'ć',
    '|': 'đ',
    '{': 'š',
    '`': 'ž',
}

def good_adjacent(c):
    return c.isalpha() or '~^}|{` .,'.count(c)

def fix_diacritics(text):
    end = len(text)-1
    text_list = list(text)
    for key, val in diacritics_map.items():
        start = 0
        pos = 0
        while pos >= 0:
            pos = text.find(key, start)
            if pos > 0 and pos < end:
                if good_adjacent(text[pos-1]) and good_adjacent(text[pos+1]):
                    text_list[pos] = val
                start = pos + 1
    return ''.join(text_list)

# see also https://stackoverflow.com/questions/75816685/regex-that-finds-groups-of-lines-where-certain-lines-within-the-group-starting-w
def clear_section_text(text):
    """ clear the text extracted by pdfminer from a PDF section of the marketing book
    """
    text = re.sub(r'^.*\n*.*\n{2,}', '', text) # remove from start, 2 following double newlines and text btwn them
    text = re.sub(r'(\n)[\d]+[\ \t]+http.*(\n)', r'\2', text) # remove note with url
    text = re.sub(r'\.\ *[\n]*\f.*[\n]*.*[\n]*', '.\n\n', text) # remove formfeed and header after fullstop
    text = re.sub(r'(.)\n*\f.*\n*.*\n*', r'\1\n\n', text) # remove formfeed and header in other cases
    text = re.sub(r'(?<=\w)-\r?\n(?=\w)', '', text) # remove hiphenation
    text = re.sub(r'(\n)(\d+[^\.]\ +)(.*)', r'\1\1\2\3', text) # add newline before note
    text = re.sub(r'(\n)[\d]+.+?([\d]+\.\ \n)', r'\1', text) # remove note containing reference to publication ?
    text = re.sub(r'(\n)[\d]+.+?([\d]+\.\n)', r'\1', text) # remove note containing reference to publication ? DA RIPETERE DOPO ...
    text = re.sub(r'(\d+\.\d+)(.+)?(\n)', r'\1\2\3\3', text) # add newline after subsection title OK
    text = re.sub(r'([\.\,\w+])[\d]+(\s)', r'\1\2', text) # remove reference to note
    text = re.sub(r'(.)\n(.)', r'\1\2', text) # replace  single newline with a space
    text = re.sub(r'(\n)[\d]+.+?([\d]+\.[\ \)]?\n)', r'\1', text) # remove note containing reference to publication ?
    text = re.sub(r'[(?<=\w)\~\^\}\|\{\`]-\r?\n*[(?=\w)\~\^\}\|\{\`]', '', text) # remove hiphenation 
    text = re.sub(r'\n+', '\n', text) # replace  multiple newlines with one
    text = re.sub(r'([\ \t])[\ \t]+', ' ', text) # replace multiple spaces with s single space
    text = re.sub(r'\ +(\n)', r'\1', text) # remove space before newline
    return text

def txt_esteban_to_json(filepath: str, es_key='Glosario en español', en_key='Glossary in English') -> str:
    with open(filepath, 'r', encoding="utf8") as f:
        language = None
        line = f.readline()
        while line:
            if len(line) <= 2 or line.startswith('#'):
                line = f.readline()
                continue
            if line.startswith(es_key):
                language = 'es'
                heading = line
                print(heading)
                line = f.readline()
                continue
            elif line.startswith(en_key):
                language = 'en'
                heading = line
                print(heading)
                line = f.readline()
                continue
            tokens = line.split()
            n_tokens = len(tokens)
            if n_tokens >= 2 and tokens[0].endswith('.'):
                first = tokens[0].replace('.', '').strip()
                number = int(first)
                term = ' '.join(tokens[1:])
                if term[-1] in ['.', ':']:
                    term = term[:-1]
                definition = f.readline()
                print(language, number, term, definition)
            line = f.readline()

def txt_pena_to_json(filepath: str) -> str:
    with open(filepath, 'r', encoding="utf8") as f:
        language = None
        line = f.readline()
        while line:
            if len(line) <= 2 or line.startswith('#'):
                line = f.readline()
                continue
            tokens = line.split()
            n_tokens = len(tokens)
            if n_tokens >= 2 and tokens[0].endswith('.'):
                first = tokens[0].replace('.', '').strip()
                number = int(first)

                language = 'es'
                line = ' '.join(tokens[1:])
                splitted = line.split(':')
                term = splitted[0]
                definition = ':'.join(splitted[1:])
                print(language, number, term, definition)

                line = f.readline().strip()
                tokens = line.split()
                assert tokens[0] == '—'
                language = 'en'
                line = ' '.join(tokens[1:])
                splitted = line.split(':')
                term = splitted[0]
                definition = ':'.join(splitted[1:])
                print(language, number, term, definition)
            line = f.readline()
