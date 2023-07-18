
import os
import re
import pandas as pd
from pdfminer.high_level import extract_text
import pdfplumber

PDFMINER = False
PDFPLUMBER = True
assert PDFMINER or PDFPLUMBER

def extract_with_pdfminer(path):
    return extract_text(path)

# see: https://stackoverflow.com/questions/66900539/how-to-stop-pdfplumber-from-reading-the-header-of-every-pages
# see: https://stackoverflow.com/questions/76292334/how-to-remove-borders-from-a-pdf-using-python-and-pdfplumber-for-azure-form-reco
def extract_with_pdfplumber(path):
    """ Here is the explanation of coords:
    x0 = % Distance of left side of character from left side of page.
    top = % Distance of top of character from top of page.
    x1 = % Distance of right side of character from left side of page.
    bottom = % Distance of bottom of the character from top of page.
    """
    text_list = []
    from_top_base = 60
    from_bottom = 40
    y_tolerance = 15
    min_indentation = 65 # for paragraph
    max_indentation = min_indentation + 20
    trailer_length = 7
    sync_tolerance = 15
    forward_step = 10
    with pdfplumber.open(path) as pdf:
        for i_page, pdf_page in enumerate(pdf.pages):
            from_top = from_top_base
            bbox = (0, from_top, pdf_page.width, pdf_page.height-from_bottom)
            page = pdf_page.within_bbox((0, from_top, pdf_page.width, pdf_page.height-from_bottom))
            if i_page == 0:
                while not page.chars[0]['text'].isnumeric() and from_top_base-from_top < 10:
                    from_top -= 2
                    page = pdf_page.within_bbox((0, from_top, pdf_page.width, pdf_page.height-from_bottom))
            lines = page.lines
            rects = page.rects
            # remove notes below small horizontal line (re-compute and re-apply bbox)
            if len(lines) == 1:
                line = lines[0]
                line_bound = line['y1']+1
                bbox = (0, from_top, pdf_page.width, pdf_page.height-line_bound)
                page = pdf_page.within_bbox(bbox)
            # remove figure by subtracting content of rectangle
            if len(rects) == 1:
                rect = rects[0]
                rect_box = (rect['x0'], rect['top'], rect['x1'], rect['bottom'])
                page = page.outside_bbox(rect_box)
            chars = page.chars
            n_chars = len(chars)
            text = page.extract_text()
            text = re.sub(r'([\ \t])[\ \t]+', ' ', text) # replace multiple spaces with s single space
            i_char = 0
            i_text = 0
            pos = 0
            n_newlines = 0
            while i_char < n_chars:
                if i_page == 0 and i_char == 0:
                    i_char += forward_step
                    continue
                char = chars[i_char]
                if not char['text'].isalnum():
                    i_char += 1
                    continue
                j_char = i_char - 1
                while j_char and not (chars[j_char]['text'].isalpha() or chars[j_char]['text'] in diacritics):
                    j_char -= 1
                prev = chars[j_char]
                if char['x0'] > min_indentation and \
                   char['x0'] < max_indentation and \
                   (prev['y0']-char['y0'] > y_tolerance) or (i_char == 0 and (char['text'].isupper() or not char['text'].isalpha())):
                    trailer = ''.join([char['text'] for char in chars[i_char:i_char+trailer_length]])
                    trailer = re.sub(r'([\ \t])[\ \t]+', ' ', trailer) # replace multiple spaces with s single space
                    pos = text.find(trailer, i_text)
                    if pos >= 0 and abs(pos-i_char) <= sync_tolerance+n_newlines:
                        text = text[:pos]+'\n'+text[pos:]
                        n_newlines += 1
                        i_text = pos + forward_step
                        i_char += forward_step
                i_char += 1
            text_list.append(text)
    return '\f'.join(text_list)

def extract_marketing_book(path='/Users/giovanni/OneDrive/_Progetti/_WE-COLLAB/PR2/materials', in_name='Marketing_book.xlsx', out_name='book.xlsx'):
    in_path = os.path.join(path, in_name)
    out_path = os.path.join(path, out_name)
    # read Marketing_book.xlsx as a Panda dataframe
    excel_data = pd.read_excel(in_path)
    data = pd.DataFrame(excel_data, columns=['Chapter', 'Subchapter', 'Text'])
    # for each row in xslx read the 3 columns and
    # for index, row in list(data.iterrows())[:1]:
    for index, row in data.iterrows():
        # copy the text (3rd column) to text_1
        text_1 = row['Text']
        # compute name of PDF file for that section
        chapter_name = row['Chapter']
        chapter = chapter_name.split()[0][:-1]
        section_name = '{}-{} {}.pdf'.format(chapter, index+1, row['Subchapter'])
        section_path = os.path.join(path, section_name)
        print('+++ SECTION', section_path)
        if PDFMINER:
            text = extract_with_pdfminer(section_path)
        elif PDFPLUMBER:
            text = extract_with_pdfplumber(section_path)
        text = fix_diacritics(text)
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
    '@': 'Ž',
    '`': 'ž',
}
diacritics = list(diacritics_map.keys())

def fix_diacritics(text):
    end = len(text)-1
    text_list = list(text)
    for key, val in diacritics_map.items():
        start = 0
        pos = 0
        while pos >= 0:
            pos = text.find(key, start)
            if pos > 0 and pos < end:
                text_list[pos] = val
                start = pos + 1            
    return ''.join(text_list)

# see also https://stackoverflow.com/questions/75816685/regex-that-finds-groups-of-lines-where-certain-lines-within-the-group-starting-w
def clear_section_text(text):
    """ clear the text extracted by pdfminer from a PDF section of the marketing book
    """
    if PDFMINER:
        text = re.sub(r'^.*\n*.*\n{2,}', '', text) # remove from start, 2 double newlines and text btwn them
        text = re.sub(r'(\n)[\d]+[\ \t]+http.*(\n)', r'\2', text) # remove note with url
        text = re.sub(r'\.\ *[\n]*\f.*[\n]*.*[\n]*', '.\n\n', text) # remove formfeed and header after fullstop
        text = re.sub(r'(.)\n*\f.*\n*.*\n*', r'\1\n\n', text) # remove formfeed and header in other cases
    if PDFPLUMBER:
        text = re.sub(r'(\w)\f(\w)', r'\1 \2', text) # replace form-feed between words with a space
        text = re.sub('\f', '\n\n', text) # replace form-feed with 2 newlines
    text = re.sub(r'(?<=\w)-\r?\n(?=\w)', '', text) # remove simple hiphenation
    if PDFMINER:
        text = re.sub(r'(\n)(\d+[^\.]\ +)(.*)', r'\1\1\2\3', text) # add newline before note
        text = re.sub(r'(\n)[\d]+.+?([\d]+\.\ \n)', r'\1', text) # remove note containing reference to publication ?
        text = re.sub(r'(\n)[\d]+.+?([\d]+\.\n)', r'\1', text) # remove note containing reference to publication ? DA RIPETERE DOPO ...
    text = re.sub(r'(\d+\.\d+)(.+)?(\n)', r'\1\2\3\3', text) # add newline after subsection title OK
    text = re.sub(r'([\.\,\w+])[\d]+(\s)', r'\1\2', text) # remove reference to note
    text = re.sub(r'(.)\n(.)', r'\1 \2', text) # replace  single newline with a space
    text = re.sub(r'(\n)[\d]+.+?([\d]+\.[\ \)]?\n)', r'\1', text) # remove note containing reference to publication ?
    text = re.sub(r'([(?<=\w)\~\^\}\|\{\@\`])-\r?\n*([(?=\w)\~\^\}\|\{\@\`])', r'\1\2', text) # remove residual hiphenation 
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
