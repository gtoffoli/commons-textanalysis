import re
import pyphen
import string
from collections import defaultdict
from bs4 import BeautifulSoup

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
