import re
import pyphen
import string
from collections import defaultdict
from textract import process
from bs4 import BeautifulSoup

def get_document_text(document, return_has_text=False):
    has_text = False
    text = ''
    version = document.latest_version
    mimetype = version.mimetype
    encoding = 'utf8'
    if mimetype.count('text'): # if mimetype.endswith('text'):
        has_text = True
    if mimetype.count('text/plain'):
        has_text = True
        if not return_has_text:
            text = process(version.file.path, encoding=encoding, extension='txt')
    elif mimetype.count('pdf'): # elif mimetype.endswith('pdf'):
        has_text = True
        if not return_has_text:
            text = process(version.file.path, encoding=encoding, extension='pdf')
    elif mimetype.count('rtf'): # elif mimetype.endswith('rtf'):
        has_text = True
        if not return_has_text:
            text = process(version.file.path, encoding=encoding, extension='rtf')
    elif mimetype.count('msword'): # elif mimetype.endswith('msword'):
        has_text = True
        if not return_has_text:
            text = process(version.file.path, encoding=encoding, extension='doc')
    elif mimetype.count('officedocument.wordprocessingml') and mimetype.count('document'):
        has_text = True
        if not return_has_text:
            text = process(version.file.path, encoding=encoding, extension='docx')
    elif mimetype.count('officedocument.presentationml'):
        has_text = True
        if not return_has_text:
            text = process(version.file.path, encoding=encoding, extension='pptx')
    elif mimetype.count('officedocument.spreadsheetml'):
        has_text = True
        if not return_has_text:
            text = process(version.file.path, encoding=encoding, extension='xlsx')
    else:
        split_label = document.label.split('.')
        if len(split_label) > 1:
            extension = split_label[-1]
            if extension in ['csv', 'doc', 'docx', 'eml', 'epub', 'htm', 'html', 'json', 'msg', 'odt', 'pdf', 'pptx', 'ps', 'rtf', 'txt', 'xslx', 'xss',]:
                has_text = True
                if not return_has_text:
                    text = process(version.file.path, encoding=encoding, extension=extension)
    if return_has_text:
        return has_text
    else:
        try:
            text = text.decode()
        except (UnicodeDecodeError, AttributeError):
            pass
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

def lemmas_to_colors(lemmas, colors):
    """ create a dict which maps from lemmas defined by an ordered list of the format [text, count]
        to colors defined by an ordered list of the form [colorname, colorcode] """
    lemmas_colors = {}
    for i, lemma in enumerate(lemmas):
        lemmas_colors[lemma[0]] = colors[i][1]
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
