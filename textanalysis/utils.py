import re
import pyphen
import string
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
