from six import BytesIO
import os
import re
import json
import csv
from io import StringIO
import pyphen
import string
from collections import defaultdict
import urllib.parse
import requests
import tempfile
import readability
import textract
import xmltodict
from bs4 import BeautifulSoup
from django.conf import settings
from django.utils.translation import gettext_lazy as _

# some default values from https://github.com/explosion/spaCy/blob/master/spacy/displacy/render.py
DEFAULT_LANG = "en"
DEFAULT_DIR = "ltr"
DEFAULT_ENTITY_COLOR = "#ddd"
DEFAULT_LABEL_COLORS = {
    "ORG": "#7aecec",
    "PRODUCT": "#bfeeb7",
    "GPE": "#feca74",
    "LOC": "#ff9561",
    "PERSON": "#aa9cfc",
    "PER": "#aa9cfc",
    "NORP": "#c887fb",
    "FAC": "#9cc9cc",
    "EVENT": "#ffeb80",
    "LAW": "#ff8197",
    "LANGUAGE": "#ff8197",
    "WORK_OF_ART": "#f0d0ff",
    "DATE": "#bfe1d9",
    "TIME": "#bfe1d9",
    "MONEY": "#e4e7d2",
    "QUANTITY": "#e4e7d2",
    "ORDINAL": "#e4e7d2",
    "CARDINAL": "#e4e7d2",
    "PERCENT": "#e4e7d2",
}

mimetype_extension_list = (
    ('text/plain', 'txt'),
    ('pdf', 'pdf'),
    ('rtf', 'rtf'),
    ('msword', 'doc'),
    ('officedocument.wordprocessingml', 'docx'),
    ('officedocument.presentationml', 'pptx'),
    ('officedocument.spreadsheetml', 'xlsx'),
)

def get_file_text(file, content_type, title=''):
    encoding = 'utf8'
    f = tempfile.NamedTemporaryFile(dir='/tmp', mode='w+b', delete=False)
    n = f.write(file)
    print('get_file_text', n)
    if content_type.count('pdf'):
        text = textract.process(f.name, encoding=encoding, extension='pdf')
    elif content_type.count('rtf'):
        text = textract.process(f.name, encoding=encoding, extension='rtf')
    elif content_type.count('msword'):
        text = textract.process(f.name, encoding=encoding, extension='doc')
    elif content_type.count('officedocument.wordprocessingml') and content_type.count('document'):
        text = textract.process(f.name, encoding=encoding, extension='docx')
    elif content_type.count('officedocument.presentationml'):
        text = textract.process(f.name, encoding=encoding, extension='pptx')
    elif content_type.count('officedocument.spreadsheetml'):
        text = textract.process(f.name, encoding=encoding, extension='xlsx')
    f.close()
    err = None
    try:
        text = text.decode()
    except (UnicodeDecodeError, AttributeError) as err:
        return '', response, err
    return title, text, err

def get_web_resource_text(url):
    fileid = get_googledoc_fileid(url)
    if fileid:
        return get_google_doc_text(None, fileid=fileid)
    err = None
    try:
        response = requests.get(url)
    except ConnectionError as err:
        return '', response, err
    except requests.exceptions.RequestException as err:
        return '', response, err
    if not (response.status_code == 200):
        return '', response, err
    text = ''
    title = ''
    encoding = 'utf8'
    content_type = response.headers['content-type']
    print('---------------- get_web_resource_text', response.status_code, content_type, len(response.text))
    if content_type.count('text/plain'):
        text = response.text
    elif content_type.count('text/html') or url.endswith('.htm'):
        text = response.text
        doc = readability.Document(text)
        print('---------------- get_web_resource_text', doc, doc.title())
        text = doc.summary()
        title = doc.title()
        text = extract_annotate_with_bs4(text)
    else:
        # with tempfile.NamedTemporaryFile(dir='/tmp', mode='w+b') as f:
        with tempfile.NamedTemporaryFile(dir='/tmp', mode='w+b', delete=False) as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)   
        if content_type.count('pdf'):
            text = textract.process(f.name, encoding=encoding, extension='pdf')
        elif content_type.count('rtf'):
            text = textract.process(f.name, encoding=encoding, extension='rtf')
        elif content_type.count('msword'):
            text = textract.process(f.name, encoding=encoding, extension='doc')
        elif content_type.count('officedocument.wordprocessingml') and content_type.count('document'):
            text = textract.process(f.name, encoding=encoding, extension='docx')
        elif content_type.count('officedocument.presentationml'):
            text = textract.process(f.name, encoding=encoding, extension='pptx')
        elif content_type.count('officedocument.spreadsheetml'):
            text = textract.process(f.name, encoding=encoding, extension='xlsx')
        f.close()
        try:
            text = text.decode()
        except (UnicodeDecodeError, AttributeError) as err:
            return '', response, err
    # return text, response, err
    return title, text, response, err

def get_document_text(document, return_has_text=False):
    has_text = False
    text = ''
    version = document.latest_version
    # mimetype = version.mimetype
    mimetype = version.mimetype or document.file_mimetype
    encoding = 'utf8'
    if mimetype.count('text'): # if mimetype.endswith('text'):
        has_text = True
    if mimetype.count('text/plain'):
        has_text = True
        if not return_has_text:
            text = textract.process(version.file.path, encoding=encoding, extension='txt')
    elif mimetype.count('pdf'): # elif mimetype.endswith('pdf'):
        has_text = True
        if not return_has_text:
            text = textract.process(version.file.path, encoding=encoding, extension='pdf')
    elif mimetype.count('rtf'): # elif mimetype.endswith('rtf'):
        has_text = True
        if not return_has_text:
            text = textract.process(version.file.path, encoding=encoding, extension='rtf')
    elif mimetype.count('msword'): # elif mimetype.endswith('msword'):
        has_text = True
        if not return_has_text:
            text = textract.process(version.file.path, encoding=encoding, extension='doc')
    elif mimetype.count('officedocument.wordprocessingml') and mimetype.count('document'):
        has_text = True
        if not return_has_text:
            text = textract.process(version.file.path, encoding=encoding, extension='docx')
    elif mimetype.count('officedocument.presentationml'):
        has_text = True
        if not return_has_text:
            text = textract.process(version.file.path, encoding=encoding, extension='pptx')
    elif mimetype.count('officedocument.spreadsheetml'):
        has_text = True
        if not return_has_text:
            text = textract.process(version.file.path, encoding=encoding, extension='xlsx')
    else:
        split_label = document.label.split('.')
        if len(split_label) > 1:
            extension = split_label[-1]
            if extension in ['csv', 'doc', 'docx', 'eml', 'epub', 'htm', 'html', 'json', 'msg', 'odt', 'pdf', 'pptx', 'ps', 'rtf', 'txt', 'xslx', 'xss',]:
                has_text = True
                if not return_has_text:
                    text = textract.process(version.file.path, encoding=encoding, extension=extension)
    if return_has_text:
        return has_text
    else:
        try:
            text = text.decode()
        except (UnicodeDecodeError, AttributeError):
            pass
        return text

def get_googledoc_fileid(document_url):
    """
    if document_url is a valid url of a Google Document or a Google Presentation,
    return the fileid to be passed to googleapis; else return None
    """
    if not document_url.startswith('https://docs.google.com'):
        return None
    if not (document_url.count('/document/d/') or document_url.count('/presentation/d/')):
        return None
    matches = re.findall("/d/([a-zA-Z0-9-_]+)", document_url)
    if len(matches)==1:
        return matches[0]
    else:
        return None   

def get_googledoc_name_type(document_url, fileid=None):
    """
    get name and type of a Google Document or a Google Presentation
    """
    if not fileid:
        fileid = get_googledoc_fileid(document_url)
    endpoint = settings.GOOGLE_DRIVE_URL
    url = '{}/{}'.format(endpoint, fileid)
    params = {'key': settings.GOOGLE_KEY, }
    params['fields'] = 'name,mimeType'
    querystring = urllib.parse.urlencode(params)
    response = requests.get('{}?{}'.format(url, querystring))
    if response.status_code != requests.codes.ok:
        return response.status_code, _('bad response status'), ''
    data = response.json()
    return response.status_code, data['name'], data['mimeType']

def get_googledoc_text(document_url, fileid=None):
    """
    extract the text from a Google Document or a Google Presentation
    """
    if not fileid:
        fileid = get_googledoc_fileid(document_url)
    if not fileid:
        return _('invalid document url')
    endpoint = settings.GOOGLE_DRIVE_URL
    url = '{}/{}/export'.format(endpoint, fileid)
    params = {'key': settings.GOOGLE_KEY, }
    params['mimeType'] = 'text/plain'
    querystring = urllib.parse.urlencode(params)
    response = requests.get('{}?{}'.format(url, querystring))
    if response.status_code != requests.codes.ok:
        return _('bad response status')
    text = response.content
    try:
        text = text.decode()
    except (UnicodeDecodeError, AttributeError):
        return _('unicode decode error')
    return text

def extract_annotate_with_bs4(html):
    soup = BeautifulSoup(html, 'lxml')
    headings = soup.find_all(re.compile('h.+'))
    for heading in headings:
        name = heading.name
        level = name[1:]
        if level.isdigit():
            text = heading.text
            if text and not text[-1] in string.punctuation:
                heading.append('.')
    lis = soup.find_all('li')
    for li in lis:
        text = li.text
        if text:
            if not text[-1] in string.punctuation:
                li.append(';')
    return soup.get_text()

# currently use hyphenation as a proxy of syllabification
class GenericSyllabizer():

    def __init__(self, language_code):
        if language_code in pyphen.LANGUAGES:
            self.dic = pyphen.Pyphen(lang=language_code)
        else:
            self.dic = None

    def syllabize(self, word):
        if self.dic:
            hyphenated = self.dic.inserted(word)
            return hyphenated.split('-')
        else:
            return []

def is_ajax(request): 
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'

def add_to_default_dict(default_dict, text):
    """ If text all UPPER or all lower, add it as is.
        If it is mixed-case, add it lowered if already present lower
                        else add it as it is.
    """
    if (len(text)>1 and text.isupper()) or text.islower():
        default_dict[text] += 1
    elif default_dict.get(text.lower(), ''):
        default_dict[text.lower()] += 1
    else:
        default_dict[text] += 1

def token_text(token, text):
    return text[token['start']:token['end']]

class MATTR():
    """ Implementation of the Moving-Average Type–Token Ratio (MATTR) algorithm
        see: Michael A. Covington & Joe D. McFall (2010) Cutting the Gordian Knot:
        The Moving-Average Type–Token Ratio (MATTR),
        Journal of Quantitative Linguistics, 17:2, 94-100, DOI: 10.1080/09296171003643098
        As a border case, returns the traditional TTR ratio.
    """

    def __init__(self, text, tokens, W=500):
        self.text = text
        self.tokens = tokens
        self.W = W # the window size
        self.frequencies = defaultdict(int)
        self.i_token = 0
        self.n_words = 0
        self.total_words = 0

    def add_token(self):
        text_in = token_text(self.tokens[self.i_token], self.text)
        n = self.frequencies[text_in]
        if n == 0:
            self.n_words += 1
        self.frequencies[text_in] += 1
        if self.i_token >= self.W:
            text_out = token_text(self.tokens[self.i_token - self.W], self.text)
            n = self.frequencies[text_out]
            if n == 1:
                self.n_words -= 1
            self.frequencies[text_out] -= 1
            self.total_words += self.n_words
        self.i_token +=1

    def get_average(self):
        n_tokens = len(self.tokens)
        n_windows = n_tokens - self.W + 1
        if self.W and n_windows >= 1:
            return self.total_words / n_windows / self.W
        else:
            return self.n_words / n_tokens

def lemmas_to_colors(lemmas, color_list, color_dict):
    """ create a dict which maps from lemmas defined by an ordered list of the format [text, count]
        to colors defined by an ordered list of the form [colorname, colorcode] """
    lemmas_colors = {}
    for i, lemma in enumerate(lemmas):
        lemmas_colors[lemma[0]] = color_dict[color_list[i]]
    print(lemmas_colors)
    return lemmas_colors

class LemmaPosDict():

    def __init__(self, doc_dicts, pos_list=['NOUN', 'PROPN', 'VERB', 'ADJ', 'ADV',], unique=True):
        """
            unique = True instructs to consider only the presence or not of the lemma in a document
            unique = False instructs to consider the no. occurrences of the lemma in a document
        """
        self.doc_dicts = doc_dicts
        self.language = doc_dicts[0]['language']
        self.pos_list = pos_list
        self.unique = unique
        self.n_docs = len(doc_dicts)
        self.range = range(self.n_docs)
        self.lemma_dict = None

    def make(self, pos_list=None):
        """ given a list of json docs and a set of pos, make a dict of items having a lemma as key
            and, as value, a list of occurrence counts, one for doc, in the same order   
        """
        self.lemma_dict = defaultdict(lambda: [0] * len(self.doc_dicts))
        if not pos_list:
            pos_list = self.pos_list
        for i, doc_dict in enumerate(self.doc_dicts):
            tokens = doc_dict['tokens']
            for token in tokens:
                pos = token['pos']
                if pos in self.pos_list:
                    lemma = token['lemma']
                    key = lemma + '_' + pos
                    if self.unique:
                        self.lemma_dict[key][i] = 1
                    else:
                        self.lemma_dict[key][i] += 1

    def get_dict(self):
        """ return the lemma-counts dict made with make """
        assert self.lemma_dict
        return self.lemma_dict

    def get_counts(self, i, j=[], pos_list=[], levels_list=[], weight_distance=False):
        """ using the lemma-counts dict made with make, return 2 aggregate values
        - n_self is the no. of lemmas occurring in the i-th doc  
        - n_union is the no. of lemmas occurring in the i-th doc and at least in one doc in the other set
        - n_diff_1 is the no. of lemmas occurring in the i-th doc and not in any doc of the other set
        - n_diff_2 is the no. of lemmas occurring at least on doc of the other set and not in the i-th doc
        input:
            i is a document index in doc_dicts
            j is a list of doc indexes; if empty, it stays for all documents but i-th
            pos_list can be used to specify a non-empty list different than the default one
            levels_list is not yet implemented
            weight_distance is not yet implemented
        """
        assert self.lemma_dict
        assert not i in j
        if levels_list:
            # load basic voabulary for language
            pass
        pos_list = pos_list or self.pos_list
        n_self = n_union = n_diff_1 = n_diff_2 = 0
        for key, counts in self.lemma_dict.items():
            pos = key.split('_')[-1]
            if not pos_list or pos in pos_list:
                if not j:
                    # if this item is present, it come from at least one doc
                    n_union += 1
                    count_others = sum([counts[k] for k in self.range if not k==i])
                    if counts[i]:
                        n_self += 1
                        if not count_others:
                            n_diff_1 +=1
                    elif count_others:
                        n_diff_2 +=1
                else:
                    count_others = sum([counts[k] for k in j])
                    if counts[i] or count_others:
                        if counts[i] and count_others:
                            n_self += 1
                            n_union += 1
                        elif count_others:
                            n_diff_2 +=1
                        else:
                            n_self += 1
                            n_diff_1 +=1
        return {'n_self': n_self, 'n_union': n_union, 'n_diff_1': n_diff_1, 'n_diff_2': n_diff_2}


def read_input_file(filepath: str) -> str:
    """ read_input_file
    Just read text from a file.
    """
    with open(filepath, 'r', encoding="utf8") as f:
        xml_str = f.read()
    return xml_str

def parse_xml(xml_str: str) -> str:
    """ parse_xml
    Takes an xml string and returns the json equivalent.
    """
    return json.dumps(xmltodict.parse(xml_str))

# define the sort order, useful for the rendeing
all_concept_columns = ['id', 'subjects',]
all_lang_columns = ['lang', 'definition', 'def. source',]
all_term_columns = ['term', 'type', 'POS', 'status', 'reliability', 'term source', 'context',]

def tbx_xml_2_dict(tbx_str: str, split_subjects=False) -> dict:
    """ tbx_xml_2_dict
    Takes an xml string and returns the equivalent Python dict slightly simpliflied.
    Adds an 'index' section intended to make easier the terminology/glossary rendering in tabular form.
    """
    json_str = parse_xml(tbx_str)

    # specify how to flatten the tbx structure
    json_str = json_str.replace('@xml:lang', 'lang')
    json_str = json_str.replace('"@type": "reliabilityCode", "#text":', '"reliabilityCode":')
    json_str = json_str.replace('"@type": "termType", "#text":', '"termType":')
    json_str = json_str.replace('"@type": "subjectField", "#text":', '"subjectField":')
    json_str = json_str.replace('"@type": "administrativeStatus", "#text":', '"administrativeStatus":')
    json_str = json_str.replace('"@type": "context", "#text":', '"context":')
    json_str = json_str.replace('"@type": "partOfSpeech", "#text":', '"partOfSpeech":')
    json_str = json_str.replace('"@type": "definition", "#text":', '"definition":')
    json_str = json_str.replace('"@type": "source", "#text":', '"source":')

    py_dict = json.loads(json_str)

    langs = set()
    columns = set(['id', 'lang', 'term',])
    concepts = py_dict['tbx']['text']['body']['conceptEntry']
    concept_dicts = []
    for concept in concepts:
        concept_dict = {'id': concept['@id']}
        lang = type(concept['langSec']) is dict and concept['langSec'].get('lang', None)
        if lang:
            concept['langSec'] = [{'lang': lang, 'termSec': concept['langSec']['termSec']}]
        subjectField = concept.get('descrip', '')
        subjects = subjectField and subjectField.get('subjectField', '') or ''
        if subjects:
            columns.add('subjects')
            if split_subjects:
                subjects = subjects.split(';') or []
        concept_dict['subjects'] = subjects
        # each conceptEntry can contain one or more langSec
        lang_dicts = []
        for lang_item in concept['langSec']:
            lang = lang_item['lang']
            langs.add(lang)
            lang_dict = {'lang': lang}
            descripGrp = lang_item.get('descripGrp', None)
            if descripGrp:
                descrip = descripGrp.get('descrip', None)
                if descrip:
                    definition = descrip.get('definition', None)
                    if definition:
                        definition = join_blankspaces(definition)
                        lang_dict['definition'] = definition
                        columns.add('definition')
                admin = descripGrp.get('admin', None)
                if admin:
                    source = admin.get('source', None)
                    if source:
                        # lang_dict['source'] = source
                        lang_dict['def. source'] = source
                        columns.add('def. source')
            # each langSec can contain one or more termSec
            term_items = lang_item['termSec']
            if not type(term_items) == list:
                term_items = [term_items]
            term_dicts = []
            for term_item in term_items:
                term_dict = {'term': term_item['term']}
                termType = term_item.get('termType', None)
                if termType:
                    # term_dict['termType'] = termType
                    term_dict['type'] = termType
                    columns.add('type')
                partOfSpeech = term_item.get('partOfSpeech', None)
                if partOfSpeech:
                    # term_dict['partOfSpeech'] = partOfSpeech
                    term_dict['POS'] = partOfSpeech
                    columns.add('POS')
                reliabilityCode = term_item.get('reliabilityCode', None)
                if reliabilityCode:
                    # term_dict['reliabilityCode'] = reliabilityCode
                    term_dict['reliability'] = reliabilityCode
                    columns.add('reliability')
                administrativeStatus = term_item.get('administrativeStatus', None)
                if administrativeStatus:
                    # term_dict['administrativeStatus'] = administrativeStatus
                    term_dict['status'] = administrativeStatus.replace('Term-admn-sts', '')
                    columns.add('status')
                # each termSec can contain one or more termNote
                term_notes = term_item.get('termNote', [])     
                if term_notes and not type(term_notes) == list:
                    term_notes = [term_notes]
                for term_note in term_notes:
                    partOfSpeech = term_note.get('partOfSpeech', None)
                    if partOfSpeech:
                        # term_dict['partOfSpeech'] = partOfSpeech
                        term_dict['POS'] = partOfSpeech
                        columns.add('POS')
                    termType = term_note.get('termType', None)
                    if termType:
                        # term_dict['termType'] = termType
                        term_dict['type'] = termType
                        columns.add('type')
                    administrativeStatus = term_note.get('administrativeStatus', None)
                    if administrativeStatus:
                        # term_dict['administrativeStatus'] = administrativeStatus.replace('Term-admn-sts', '')
                        term_dict['status'] = administrativeStatus.replace('Term-admn-sts', '')
                        columns.add('status')
                # each termSec can contain zero, one or more (?) descrip items
                term_descrips = term_item.get('descrip', [])
                if term_descrips and not type(term_descrips) == list:
                    term_descrips = [term_descrips]
                for term_descrip in term_descrips:
                    reliabilityCode = term_descrip.get('reliabilityCode', None)
                    if reliabilityCode:
                        # term_dict['reliabilityCode'] = reliabilityCode
                        term_dict['reliability'] = reliabilityCode
                        columns.add('reliability')
                # each termSec can contain zero or one descripGrp
                descripGrp = term_item.get('descripGrp', None)     
                if descripGrp:
                    descrip = descripGrp.get('descrip', None)
                    if descrip:
                        context = descrip.get('context', None)
                        if context:
                            context = join_blankspaces(context)
                            term_dict['context'] = context
                            columns.add('context')
                    admin = descripGrp.get('admin', None)
                    if admin:
                        source = admin.get('source', None)
                        if source:
                            # term_dict['source'] = source
                            term_dict['term source'] = source
                            columns.add('term source')
                term_dicts.append(term_dict)
            lang_dict['termSec'] = term_dicts
            lang_dicts.append(lang_dict)
        lang_dicts.sort(key=lambda x: x['lang'])
        concept_dict['langSec'] = lang_dicts
        concept_dicts.append(concept_dict)
    langs = sorted(list(langs))
    concept_columns = [c for c in all_concept_columns if c in columns]
    lang_columns = [c for c in all_lang_columns if c in columns]
    term_columns = [c for c in all_term_columns if c in columns]
    return {'tbx': {'text': {'index': {'langs': langs, 'conceptColumns': concept_columns, 'langColumns': lang_columns, 'termColumns': term_columns,}, 'body': {'conceptEntry': concept_dicts}}}}

def tbx_dict_2_tsv(tbx_dict: dict) -> str:
    """
    Takes a Python dict representing an xml-tbx document parsed with tbx_xml_2_dict, simpliflied but enriched with an 'index' section.
    Produces a text file in TSV format (tab-separated values), whose columns are specified by the 'index' section.
    """
    text = tbx_dict['tbx']['text']
    index = text['index']
    concept_columns = index['conceptColumns']
    concept_blanks = ['' for key in concept_columns]
    lang_columns = index['langColumns']
    lang_blanks = ['' for key in lang_columns]
    term_columns = index['termColumns']
    concept_dicts = text['body']['conceptEntry']
    # builds the heading row
    col_names = concept_columns + lang_columns + term_columns
    headings = '\t'.join(col_names)
    lines = [headings]
    # loops on the concept list
    for concept_dict in text['body']['conceptEntry']:
        concept_values = [concept_dict.get(key, '') for key in concept_columns]
        # loops on the language list
        lang_dicts = concept_dict['langSec']
        i_lang = 0
        for lang_dict in concept_dict['langSec']:
            lang_values = [lang_dict.get(key, '') for key in lang_columns]
            # loops on the term list
            i_term = 0
            for term_dict in lang_dict['termSec']:
                values = []
                term_values = [term_dict.get(key, '') for key in term_columns]
                if i_lang == 0 and i_term == 0:
                    values += concept_values
                else:
                    values += concept_blanks
                if i_term == 0:
                    values += lang_values
                else:
                    values +=lang_blanks
                values += term_values
                lines.append('\t'.join(values))
                i_term += 1 
            i_lang += 1
    csv_data = '\n'.join(lines)
    return csv_data

def tbx_tsv_2_dict(tsv_data: str) -> dict:
    lines = tsv_data.splitlines()
    reader = csv.reader(lines, delimiter='\t')
    parsed_tsv = list(reader)
    columns = parsed_tsv[0]
    rows = parsed_tsv[1:]
    row_dicts = []
    for row in rows:
        row_dicts.append(dict(zip(columns, row)))
    langs = set()
    for d in row_dicts:
        if d['lang']:
            langs.add(d['lang'])
    langs = sorted(list(langs))
    concept_columns = [c for c in all_concept_columns if c in columns]
    lang_columns = [c for c in all_lang_columns if c in columns]
    term_columns = [c for c in all_term_columns if c in columns]
    row_dicts.reverse()
    concept_dicts = []
    lang_dicts = []
    term_dicts = []
    for row in row_dicts:
        term_dict = {}
        for c in term_columns:
            if row[c]:
                term_dict[c] = row[c]
        term_dicts.append(term_dict)
        if row['lang']:
            lang_dict = {}
            for c in lang_columns:
                if row[c]:
                    lang_dict[c] = row[c]
            term_dicts.reverse()
            lang_dict['termSec'] = term_dicts
            term_dicts = []
            lang_dicts.append(lang_dict)
        if row['id']:
            concept_dict = {}
            for c in concept_columns:
                if row[c]:
                    if c == 'subjects':
                        concept_dict[c] = [row[c]]
                    else:
                        concept_dict[c] = row[c]
            lang_dicts.reverse()
            concept_dict['langSec'] = lang_dicts
            lang_dicts = []
            concept_dicts.append(concept_dict)
    concept_dicts.reverse()
    tbx_dict = {'tbx': {'text': {'index': {'langs': langs, 'conceptColumns': concept_columns, 'langColumns': lang_columns, 'termColumns': term_columns,}, 'body': {'conceptEntry': concept_dicts}}}}
    return tbx_dict

def write_output_file(filename: str, contents: str) -> None:
    """ _write_output_file
    Just writes text to a file.
    """
    with open(filename, 'w',  encoding="utf8") as file_obj:
        file_obj.write(contents)
        file_obj.close()

def tbxfile_to_json(path: str, filename: str) -> None:
    """ tbxfile_to_json
    Reads from file and parses an xml string in TBX format.
    Converts to JSON the parsed object.
    Removes some syntax derived from xml.
    Writes the result string to a .json file in the same folder.
    """
    tbx_filename = os.path.join(path, filename+'.tbx')
    json_filename = os.path.join(path, filename+'.json')
    tbx_str = read_input_file(tbx_filename)
    json_str = json.dumps(tbx_xml_2_dict(tbx_str, split_subjects=True))
    write_output_file(json_filename, json_str)

def tbxfile_to_csv(path: str, filename: str) -> None:
    """ tbxfile_to_csv
    Reads from file and parses an xml string in TBX format.
    Converts to JSON the parsed object.
    Removes some syntax derived from xml.
    Converts JSON to CSV (with tab separated values)
    Writes the result string to a .csv file in the same folder.
    """
    tbx_filename = os.path.join(path, filename+'.tbx')
    csv_filename = os.path.join(path, filename+'.csv')
    tbx_str = read_input_file(tbx_filename)
    tbx_dict = tbx_xml_2_dict(tbx_str)
    csv_str = tbx_dict_2_tsv(tbx_dict)
    write_output_file(csv_filename, csv_str)

def csvfile_to_json(path: str, filename: str) -> None:
    """ csvfile_to_json
    Reads a CSV file (with tab separated values) and parses it to a list of lists.
    First row contains a list of TBX field names related to concept, language and term in the order.
    Parse the other rows, in reverse order, to reconstruct term, language and concept sub-dicts.
    Writes the resulting dict as a file in JSON format in the same folder.
    """
    csv_filename = os.path.join(path, filename+'.csv')
    json_filename = os.path.join(path, filename+'.json')
    tsv_data = read_input_file(csv_filename)
    tbx_dict = tbx_tsv_2_dict(tsv_data)
    json_str = json.dumps(tbx_dict)
    write_output_file(json_filename, json_str)

def path_from_file_key(file_key):
    return os.path.join(settings.CORPORA, file_key)+'.spacy'

def load_corpus_metadata(file_key):
    """ reads a dictionary from a json file associated to a docbin spacy file; keys / values:
    site_id / id of the current site object at creation time
    username / username of corpus creator
    state / current access-visibility state (PRIVATE / RESTRICTED / PUBLIC)
    domains / list of BabelNet domain strings 
    """
    metadata = {}
    path = path_from_file_key(file_key).replace('.spacy', '.json')
    if os.path.exists(path):
        f = open(path)
        metadata = json.load(f)
        f.close()
    return metadata

def save_corpus_metadata(file_key, metadata):
    """ writes a list of domain strings to a json file associated to a docbin spacy file """
    path = path_from_file_key(file_key).replace('.spacy', '.json')
    data = json.dumps(metadata)
    f = open(path, 'w')
    f.write(data)
    f.close

def rename_corpus_metadata(file_key, new_file_key):
    path = path_from_file_key(file_key).replace('.spacy', '.json')
    new_path = path_from_file_key(new_file_key).replace('.spacy', '.json')
    os.rename(path, new_path)

def set_excel_header(response, filename):
    mimetype = 'application/vnd.ms-excel'
    response['Content-Type'] = '%s; charset=utf-8' % mimetype
    response['Content-Disposition'] = 'attachment; filename=%s.csv' % filename
    return response

def join_blankspaces(text):
    return ' '.join(text.split())
