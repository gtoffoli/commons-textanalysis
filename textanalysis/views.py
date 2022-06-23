from django.shortcuts import render
# Create your views here.

# -*- coding: utf-8 -*-"""

from importlib import import_module
import json
import requests
import tempfile
from collections import defaultdict, OrderedDict
from operator import itemgetter

import textract
import readability
from django.http import HttpResponseForbidden, JsonResponse
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt

from textanalysis.forms import TextAnalysisInputForm
from textanalysis.utils import GenericSyllabizer, extract_annotate_with_bs4, is_ajax

nlp_url = settings.NLP_URL
# nlp_url = 'http://localhost:8001'

obj_type_label_dict = {
'project': _('commonspaces project'),
'doc': _('document file'),
'oer': _('open educational resource'),
'pathnode': _('node of learning path'),
'lp': _('learning path'),
'resource': _('remote web resource'),
'text': _('manually input text'),
'corpus': _('text corpus'),
'': '?',
}

# from NLPBuddy
ENTITIES_MAPPING = {
    'PERSON': 'person',
    'LOC': 'location',
    'GPE': 'location',
    'ORG': 'organization',
}

# =====from NLPBuddy
POS_MAPPING = {
    'NOUN': 'nouns',
    'VERB': 'verbs',
    'ADJ': 'adjectives',
    'ADV': 'adverbs',
}

EMPTY_POS = [
    'SPACE', 'PUNCT', 'CCONJ', 'SCONJ', 'DET', 'PRON', 'ADP', 'AUX', 'PART', 'SYM',
]

postag_color = 'cornflowerBlue'
entity_color = 'tomato'
dependency_color = 'purple'

# ===== froom BRAT; see http://brat.nlplab.org/configuration.html and https://brat.nlplab.org/embed.html
collData = {
    'entity_types': [
        { 'type': 'ADJ', 'labels': ['adjective', 'adj'], 'bgColor': postag_color, 'borderColor': 'darken' }, # big, old, green, incomprehensible, first
        { 'type': 'ADP', 'labels': ['adposition', 'adp'], 'bgColor': postag_color, 'borderColor': 'darken' }, # in, to, during
        { 'type': 'ADV', 'labels': ['adverb', 'adv'], 'bgColor': postag_color, 'borderColor': 'darken' }, # very, tomorrow, down, where, there
        { 'type': 'AUX', 'labels': ['auxiliary', 'aux'], 'bgColor': postag_color, 'borderColor': 'darken' }, # is, has (done), will (do), should (do)
        { 'type': 'CONJ', 'labels': ['conjunction', 'conj'], 'bgColor': postag_color, 'borderColor': 'darken' }, # and, or, but
        { 'type': 'CCONJ', 'labels': ['coord.conj.', 'cconj'], 'bgColor': postag_color, 'borderColor': 'darken' }, # and, or, but
        { 'type': 'DET', 'labels': ['determiner', 'det'], 'bgColor': postag_color, 'borderColor': 'darken' }, # a, an, the
        { 'type': 'INTJ', 'labels': ['interjection', 'intj'], 'bgColor': postag_color, 'borderColor': 'darken' }, # psst, ouch, bravo, hello
        { 'type': 'NOUN', 'labels': ['noun', 'noun'], 'bgColor': postag_color, 'borderColor': 'darken' }, # girl, cat, tree, air, beauty
        { 'type': 'NUM', 'labels': ['numeral', 'num'], 'bgColor': postag_color, 'borderColor': 'darken' }, # 1, 2017, one, seventy-seven, IV, MMXIV
        { 'type': 'PART', 'labels': ['particle', 'part'], 'bgColor': postag_color, 'borderColor': 'darken' }, # ’s, not,
        { 'type': 'PRON', 'labels': ['pronoun', 'pron'], 'bgColor': postag_color, 'borderColor': 'darken' }, # I, you, he, she, myself, themselves, somebody
        { 'type': 'PROPN', 'labels': ['proper noun', 'propn'], 'bgColor': postag_color, 'borderColor': 'darken' }, # Mary, John, London, NATO, HBO
        { 'type': 'PUNCT', 'labels': ['punctuation', 'punct'], 'bgColor': postag_color, 'borderColor': 'darken' }, # ., (, ), ?
        { 'type': 'SCONJ', 'labels': ['sub.conj.', 'sconj'], 'bgColor': postag_color, 'borderColor': 'darken' }, # if, while, that
        { 'type': 'SYM', 'labels': ['symbol', 'sym'], 'bgColor': postag_color, 'borderColor': 'darken' }, # $, %, §, ©, +, −, ×, ÷, =, :), 😝
        { 'type': 'VERB', 'labels': ['verb', 'verb'], 'bgColor': postag_color, 'borderColor': 'darken' }, # un, runs, running, eat, ate, eating
        { 'type': 'X', 'labels': ['other', 'x'], 'bgColor': postag_color, 'borderColor': 'darken' }, # sfpksdpsxmsa
        { 'type': 'SPACE', 'labels': ['space', 'sp'], 'bgColor': postag_color, 'borderColor': 'darken' }, #

        { 'type': 'PERSON', 'labels': ['Person', 'Per'], 'bgColor': entity_color, 'borderColor': 'darken' }, # People, including fictional.
        { 'type': 'NORP', 'labels': ['NORP', 'NORP'], 'bgColor': entity_color, 'borderColor': 'darken' },  # Nationalities or religious or political groups.
        { 'type': 'FAC', 'labels': ['Facility', 'Fac'], 'bgColor': entity_color, 'borderColor': 'darken' }, # Buildings, airports, highways, bridges, etc.
        { 'type': 'ORG', 'labels': ['Organization', 'Org'], 'bgColor': entity_color, 'borderColor': 'darken' }, # Companies, agencies, institutions, etc.
        { 'type': 'GPE', 'labels': ['Geo-pol.Entity', 'GPE'], 'bgColor': entity_color, 'borderColor': 'darken' }, # Countries, cities, states.
        { 'type': 'LOC', 'labels': ['Non-GPE location', 'Loc'], 'bgColor': entity_color, 'borderColor': 'darken' }, # Non-GPE locations, mountain ranges, bodies of water.
        { 'type': 'PRODUCT', 'labels': ['Product', 'Prod'], 'bgColor': entity_color, 'borderColor': 'darken' }, # Objects, vehicles, foods, etc. (Not services.)
        { 'type': 'EVENT', 'labels': ['Event', 'Evnt'], 'bgColor': entity_color, 'borderColor': 'darken' }, # Named hurricanes, battles, wars, sports events, etc.
        { 'type': 'WORK_OF_ART', 'labels': ['Work-of-Art', 'WoA'], 'bgColor': entity_color, 'borderColor': 'darken' }, # Titles of books, songs, etc.
        { 'type': 'LAW', 'labels': ['Law', 'Law'], 'bgColor': entity_color, 'borderColor': 'darken' }, # Named documents made into laws.
        { 'type': 'LANGUAGE', 'labels': ['Language', 'Lang'], 'bgColor': entity_color, 'borderColor': 'darken' }, # Any named language. 
        { 'type': 'DATE', 'labels': ['Date', 'Date'], 'bgColor': entity_color, 'borderColor': 'darken' }, # Absolute or relative dates or periods.
        { 'type': 'TIME', 'labels': ['Time', 'Time'], 'bgColor': entity_color, 'borderColor': 'darken' }, # Times smaller than a day.
        { 'type': 'PERCENT', 'labels': ['Percent', 'Perc'], 'bgColor': entity_color, 'borderColor': 'darken' }, # Percentage, including ”%“.
        { 'type': 'MONEY', 'labels': ['Money', 'Money'], 'bgColor': entity_color, 'borderColor': 'darken' }, # Monetary values, including unit.
        { 'type': 'QUANTITY', 'labels': ['Quantity', 'Quant'], 'bgColor': entity_color, 'borderColor': 'darken' }, #  Measurements, as of weight or distance.
        { 'type': 'ORDINAL', 'labels': ['Ordinal', 'Ord'], 'bgColor': entity_color, 'borderColor': 'darken' }, # “first”, “second”, etc.
        { 'type': 'CARDINAL', 'labels': ['Cardinal', 'Card'], 'bgColor': entity_color, 'borderColor': 'darken' }, # Numerals that do not fall under another type.
        { 'type': 'MISC', 'labels': ['Miscellaneus', 'Mix'], 'bgColor': entity_color, 'borderColor': 'darken' }, # Numerals that do not fall under another type.
    ],
    'relation_types': [
        { 'type': 'acl', 'labels': ['adjectival clause', 'acl'], 'color': dependency_color},
        { 'type': 'advcl', 'labels': ['adverbial clause modifier', 'advcl'], 'color': dependency_color},
        { 'type': 'advmod', 'labels': ['adverbial modifier', 'advmod'], 'color': dependency_color},
        { 'type': 'amod', 'labels': ['adjectival modifier', 'amod'], 'color': dependency_color},
        { 'type': 'appos', 'labels': ['appositional modifier', 'appos'], 'color': dependency_color},
        { 'type': 'aux', 'labels': ['auxiliary', 'aux'], 'color': dependency_color},
        { 'type': 'case', 'labels': ['case marking', 'case'], 'color': dependency_color},
        { 'type': 'cc', 'labels': ['coordinating conjunction', 'cc'], 'color': dependency_color},
        { 'type': 'ccomp', 'labels': ['clausal complement', 'ccomp'], 'color': dependency_color},
        { 'type': 'clf', 'labels': ['classifier', 'clf'], 'color': dependency_color},
        { 'type': 'compound', 'labels': ['compound', 'compound'], 'color': dependency_color},
        { 'type': 'conj', 'labels': ['conjunct', 'conj'], 'color': dependency_color},
        { 'type': 'cop', 'labels': ['copula', 'cop'], 'color': dependency_color},
        { 'type': 'csubj', 'labels': ['clausal subject', 'csubj'], 'color': dependency_color},
        { 'type': 'dep', 'labels': ['unspecified dependency', 'dep'], 'color': dependency_color},
        { 'type': 'det', 'labels': ['determiner', 'det'], 'color': dependency_color},
        { 'type': 'discourse', 'labels': ['discourse element', 'discourse'], 'color': dependency_color},
        { 'type': 'dislocated', 'labels': ['dislocated elements', 'dislocated'], 'color': dependency_color},
        { 'type': 'expl', 'labels': ['expletive', 'expl'], 'color': dependency_color},
        { 'type': 'fixed', 'labels': ['fixed multiword expression', 'fixed'], 'color': dependency_color},
        { 'type': 'flat', 'labels': ['flat multiword expression', 'flat'], 'color': dependency_color},
        { 'type': 'goeswith', 'labels': ['goes with', 'goeswith'], 'color': dependency_color},
        { 'type': 'iobj', 'labels': ['indirect object', 'iobj'], 'color': dependency_color},
        { 'type': 'list', 'labels': ['list', 'list'], 'color': dependency_color},
        { 'type': 'mark', 'labels': ['marker', 'mark'], 'color': dependency_color},
        { 'type': 'nmod', 'labels': ['nominal modifier', 'nmod'], 'color': dependency_color},
        { 'type': 'nsubj', 'labels': ['nominal subject', 'nsubj'], 'color': dependency_color},
        { 'type': 'nummod', 'labels': ['numeric modifier', 'nummod'], 'color': dependency_color},
        { 'type': 'obj', 'labels': ['object', 'obj'], 'color': dependency_color},
        { 'type': 'obl', 'labels': ['oblique nominal', 'obl'], 'color': dependency_color},
        { 'type': 'orphan', 'labels': ['orphan', 'orphan'], 'color': dependency_color},
        { 'type': 'parataxis', 'labels': ['parataxis', 'parataxis'], 'color': dependency_color},
        { 'type': 'punct', 'labels': ['punctuation', 'punct'], 'color': dependency_color},
        { 'type': 'reparandum', 'labels': ['overridden disfluency', 'reparandum'], 'color': dependency_color},
        { 'type': 'root', 'labels': ['root', 'root'], 'color': dependency_color},
        { 'type': 'vocative', 'labels': ['vocative', 'vocative'], 'color': dependency_color},
        { 'type': 'xcomp', 'labels': ['open clausal complement', 'xcomp'], 'color': dependency_color},

        # ENGLISH
        # acl    clausal modifier of noun (adjectival clause)
        { 'type': 'acomp', 'labels': ['adjectival complement', 'acomp'], 'color': dependency_color},
        # advcl    adverbial clause modifier
        # advmod    adverbial modifier
        { 'type': 'agent', 'labels': ['agent', 'agent'], 'color': dependency_color},
        # amod    adjectival modifier
        # appos    appositional modifier
        { 'type': 'attr', 'labels': ['attribute', 'attr'], 'color': dependency_color},
        # aux    auxiliary
        { 'type': 'auxpass', 'labels': ['auxiliary (passive)', 'auxpass'], 'color': dependency_color},
        # case    case marking
        # cc    coordinating conjunction
        # ccomp    clausal complement
        # compound    compound
        # conj    conjunct
        # cop    copula
        # csubj    clausal subject
        { 'type': 'csubjpass', 'labels': ['clausal subject (passive)', 'csubjpass'], 'color': dependency_color},
        { 'type': 'dative', 'labels': ['dative', 'dative'], 'color': dependency_color},
        # dep    unclassified dependent
        # det    determiner
        # dobj    direct object
        # expl    expletive
        { 'type': 'intj', 'labels': ['interjection', 'intj'], 'color': dependency_color},
        # mark    marker
        { 'type': 'meta', 'labels': ['meta modifier', 'meta'], 'color': dependency_color},
        { 'type': 'neg', 'labels': ['negation modifier', 'neg'], 'color': dependency_color},
        { 'type': 'nn', 'labels': ['noun compound modifier', 'nn'], 'color': dependency_color},
        { 'type': 'nounmod', 'labels': ['modifier of nominal', 'nounmod'], 'color': dependency_color},
        { 'type': 'npmod', 'labels': ['noun phrase as adverbial modifier', 'npmod'], 'color': dependency_color},
        # nsubj    nominal subject
        { 'type': 'nsubjpass', 'labels': ['nominal subject (passive)', 'nsubjpass'], 'color': dependency_color},
        # nummod    numeric modifier
        { 'type': 'oprd', 'labels': ['object predicate', 'oprd'], 'color': dependency_color},
        # obj    object
        # obl    oblique nominal
        # parataxis    parataxis
        { 'type': 'pcomp', 'labels': ['complement of preposition', 'pcomp'], 'color': dependency_color},
        { 'type': 'pobj', 'labels': ['object of preposition', 'pobj'], 'color': dependency_color},
        { 'type': 'poss', 'labels': ['possession modifier', 'poss'], 'color': dependency_color},
        { 'type': 'preconj', 'labels': ['pre-correlative conjunction', 'preconj'], 'color': dependency_color},
        { 'type': 'prep', 'labels': ['prepositional modifier', 'prep'], 'color': dependency_color},
        { 'type': 'prt', 'labels': ['particle', 'prt'], 'color': dependency_color},
        # punct    punctuation
        { 'type': 'quantmod', 'labels': ['modifier of quantifier', 'punctuation'], 'color': dependency_color},
        { 'type': 'relcl', 'labels': ['relative clause modifier', 'relcl'], 'color': dependency_color},
        # root    root
        # xcomp    open clausal complement
    ],
}

"""
collData = {
    'entity_types': [
        #   The labels are used when displaying the annotation, in this case
        #   for "Person" we also provide a short-hand "Per" for cases where
        #   abbreviations are preferable
        {
            'type'   : 'Person',
            'labels' : ['Person', 'Per'],
            'bgColor': 'royalblue',
            'borderColor': 'darken'
        }
    ],
    'relation_types': [
        #   A relation takes two arguments, both are named and can be constrained
        #   as to which types they may apply to
        # dashArray allows you to adjust the style of the relation arc
        { 'type': 'Anaphora', 'labels': ['Anaphora', 'Ana'], 'dashArray': '3,3', 'color': 'purple',
          'args': [
                {'role': 'Anaphor', 'targets': ['Person'] },
                {'role': 'Entity',  'targets': ['Person'] },]
        } 
    ],
}
"""

docData = {
    # This example (from https://brat.nlplab.org/embed.html) was kept here just for reference
    'text'     : "Ed O'Kelley was the man who shot the man who shot Jesse James.",
    # The entities entry holds all entity annotations
    'entities' : [
        #   Format: [${ID}, ${TYPE}, [[${START}, ${END}]]]
        #   note that range of the offsets are [${START},${END})
        ['T1', 'Person', [[0, 11]]],
        ['T2', 'Person', [[20, 23]]],
        ['T3', 'Person', [[37, 40]]],
        ['T4', 'Person', [[50, 61]]]
    ],
    'relations': [ 
        # Format: [${ID}, ${TYPE}, [[${ARGNAME}, ${TARGET}], [${ARGNAME}, ${TARGET}]]]
        ['R1', 'Anaphora', [['Anaphor', 'T2'], ['Entity', 'T1']]]
    ],
};

def count_word_syllables(word, language_code):
    n_chars = len(word)
    word = word + '  '
    n_syllables = 0
    if language_code == 'en': # see: https://medium.com/@mholtzscher/programmatically-counting-syllables-ca760435fab4
        vowels = 'aeiouy'
        if word[0] in vowels:
            n_syllables += 1
        for index in range(1, n_chars):
            if word[index] in vowels and word[index - 1] not in vowels:
                n_syllables += 1
        if word.endswith('e'):
            n_syllables -= 1
        if word.endswith('le') and n_chars > 2 and word[-3] not in vowels:
            n_syllables += 1
        if n_syllables == 0:
            n_syllables = 1
    elif language_code == 'it': # see: https://it.comp.programmare.narkive.com/TExPlcuC/programma-di-sillabazione
        vowels = 'aeiouy'
        hard_cons = 'bcdfgjpqstvwxz'
        liquid_cons = 'hlmnr'
        cons = hard_cons + liquid_cons
        if word[0] in vowels:
            n_syllables += 1
        for index in range(1, n_chars):
            c = word[index] 
            if c in cons:
                if word[index - 1] == c:
                    n_syllables += 1
                elif c == 's':
                    pass
                elif c in liquid_cons and word[index + 1] in cons and word[index + 2] in vowels:
                    n_syllables += 1
                elif c in liquid_cons and word[index + 1] in liquid_cons and word[index + 2] in vowels:
                    n_syllables += 1
            else:
                if c == 's':
                    n_syllables += 1
                elif word[index + 1] in hard_cons and (word[index + 2] in vowels or word[index + 2] in liquid_cons):
                    n_syllables += 1
                elif word[index + 1] in liquid_cons and word[index + 2] in vowels:
                    n_syllables += 1
                elif index == n_chars-1:
                    n_syllables += 1
    elif language_code == 'es':
        from textanalysis.lang.es.utils import silabizer as es_syllabizer
        syllabizer = es_syllabizer()
        syllables = syllabizer(word)
        n_syllables = len(syllables) - 1
    elif language_code == 'el':
        from textanalysis.lang.el.utils import count_word_syllables as count_word_syllables_el
        n_syllables = count_word_syllables_el(word)
    elif language_code == 'hr':
        from textanalysis.lang.hr.slog2 import count_word_syllables as count_word_syllables_hr
        n_syllables = count_word_syllables_hr(word)
    else:
        # currently, the generic syllabyzer is based on hyphenation!
        syllabyzer = GenericSyllabizer(language_code)
        syllables = syllabyzer.syllabize(word)
        if syllables:
            n_syllables = len(syllables)
        else:
            n_syllables = n_chars/2
    return max(1, int(n_syllables))

def get_web_resource_text(url):
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
    encoding = 'utf8'
    content_type = response.headers['content-type']
    if content_type.count('text/plain'):
        text = response.text
    elif content_type.count('text/html') or url.endswith('.htm'):
        text = response.text
        text = readability.Document(text).summary()
        text = extract_annotate_with_bs4(text)
    else:
        with tempfile.NamedTemporaryFile(dir='/tmp', mode='w+b') as f:
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
    return text, response, err

def index_sentences(sentences, tokens):
    i = 0
    for sentence in sentences:
        assert sentence['start']==tokens[i]['start']
        end = sentence['end']
        sentence['start_token'] = i
        while tokens[i]['end'] < end:
            i += 1
        sentence['end_token'] = i
        i += 1

def make_sentence_tree(sentence, tokens):
    i_root = None
    i = sentence['start_token']
    if hasattr(sentence, 'root'):
        root = sentence.root
    else:
        root = None
    text = ''
    while i <= sentence['end_token']:
        token = tokens[i]
        text += token['text']
        dep = token['dep']
        # if i_root is None and dep=='ROOT':
        # see: https://github.com/explosion/spaCy/issues/10003
        # see: https://stackoverflow.com/questions/36610179/how-to-get-the-dependency-tree-with-spacy
        if i_root is None and (dep=='ROOT' or dep=='dep' or i_root==root):
            i_root = sentence['root'] = i
        elif dep:
            head = tokens[token['head']]
            if not head.get('children', []):
                head['children'] = []
            head['children'].append(i)
        i += 1
    assert i_root is not None
    sentence['root'] = i_root
    sentence['text'] = text
    return i-sentence['start_token']

def token_dependency_depth(token, depth, tokens):
    max_depth = depth
    for i in token.get('children', []):
        max_depth = max(max_depth, 1+token_dependency_depth(tokens[i], depth, tokens))
    return max_depth

def sentence_dependency_depth(sentence, tokens):
    root = tokens[sentence['root']]
    return token_dependency_depth(root, 0, tokens)

def token_dependency_distance(token, max_distance, tokens):
    i_token = token['id']
    for i in token.get('children', []):
        max_distance = max(max_distance, abs(i-i_token), token_dependency_distance(tokens[i], max_distance, tokens))
    return max_distance

def sentence_dependency_distance(sentence, tokens):
    root = tokens[sentence['root']]
    return token_dependency_distance(root, 0, tokens)       

def index_entities(ents, tokens, entity_dict):
    i = 0
    for ent in ents:
        label = ent['label']
        start = ent['start']
        end = ent['end']
        while tokens[i]['start'] < start:
            i += 1
        assert start==tokens[i]['start']
        text = ''
        try: # don't know why in one case the condition below raised exception
            while tokens[i]['end'] <= end:
                text += tokens[i]['text']
                i += 1
        except:
            pass   
        ent['text'] = text
        if not '_' in text and not text in entity_dict[label]:
            entity_dict[label].append(text)

def add_to_default_dict(default_dict, token, case_dict=None):
    if (len(token)>1 and token.isupper()) or token.islower():
        default_dict[token] +=1
    elif default_dict.get(token.lower(), ''):
        default_dict[token.lower()] +=1
    else:
        default_dict[token] +=1

def sorted_frequencies(d):
    sd =  OrderedDict(sorted(d.items(), key = itemgetter(1), reverse = True))
    return [{'key': key, 'freq': freq} for key, freq in sd.items()]

token_level_dict = defaultdict(lambda:'c2')
def map_token_pos_to_level(language_code):
    global token_level_dict
    module_name = 'textanalysis.lang.{0}.basic_vocabulary_{0}'.format(language_code)
    module = import_module(module_name)
    if hasattr(module, 'get_vocabulary'):
        token_level_dict = getattr(module, 'get_vocabulary')()
    else:
        voc = getattr(module, 'voc_'+language_code)
        for item in voc:
            assert len(item) >= 3
            key = '_'.join(item[:2])
            # token_level_dict[key] = min(item[2].lower(), token_level_dict[key])
            token_level_dict[key] = min(item[2].lower(), token_level_dict.get(key, 'c1'))

language_code_dict = {
    'english': 'en',
    'italian': 'it',
    'italiano': 'it',
    'spanish': 'es',
    'español': 'es',
    'greek': 'el',
    'greek': 'el',
    'ελληνικά': 'el',
    'croatian': 'hr',
    'hrvatski': 'hr',
    'lithuanian': 'lt',
    'lietuvių': 'lt',
}

off_error = _('sorry, it looks like the language processing service is off')

def add_level_to_frequencies(frequencies, pos):
    level_count_dict = defaultdict(int)
    for frequency in frequencies:
        key = '_'.join([frequency['key'].lower(), pos])
        level = token_level_dict.get(key, None)
        if level:
            frequency['level'] = level
            frequency[level[0]] = True
        else:
            level = 'c2'
            if frequency['key'].islower():
                frequency['level'] = 'c2'        
                frequency['c'] = True
        level_count_dict[level] += frequency['freq']
    return level_count_dict

def text_dashboard_return(request, var_dict):
    if not var_dict:
        var_dict = { 'error': off_error }
    # if request.is_ajax():
    if is_ajax(request):
        return JsonResponse(var_dict)
    else:
        return var_dict # only for manual test

# def text_dashboard(request, obj_type, obj_id, file_key='', obj=None, title='', body='', wordlists=False, readability=False, nounchunks=False, contexts=False, summarization=False):
def text_dashboard(request, obj_type='', obj_id='', file_key='', obj=None, title='', body='', wordlists=False, readability=False, nounchunks=False, contexts=False, summarization=False):
    """ here (originally only) through ajax call from the template 'vue/text_dashboard.html' """
    if readability:
        wordlists = True
    if not file_key and not obj_type in ['project', 'oer', 'lp', 'pathnode', 'doc', 'flatpage', 'resource', 'text',]:
        return HttpResponseForbidden()
    description = ''
    if file_key:
        data = json.dumps({'file_key': file_key, 'obj_type': obj_type, 'obj_id': obj_id})
    else:
        if obj_type == 'text':
            title, description, body = ['', '', request.session.get('text', '')]
        elif obj_type == 'resource':
            title = ''
            body, response, err = get_web_resource_text(obj_id)
            if not body:
                if err:
                    return text_dashboard_return(request, { 'error': err.value })
                else:
                    return text_dashboard_return(request, { 'error': response.status_code })
        else:
            from commons import text_utils
            title, description, text = text_utils.get_obj_text(obj, obj_type=obj_type, obj_id=obj_id,  return_has_text=False)
            body = '{}, {}. {}'.format(title, description, text)
        if contexts:
            return {'text': body}
        data = json.dumps({'text': body})
    endpoint = nlp_url + '/api/analyze'
    try:
        response = requests.post(endpoint, data=data)
        print('text_dashboard ok')
    except:
        response = None
        print('text_dashboard ko')
    if not response or response.status_code!=200:
        print('text_dashboard', response.status_code)
        return text_dashboard_return(request, {})
    analyze_dict = response.json()
    if contexts:
        return {'text': analyze_dict['text'], 'language': analyze_dict['language']}
        
    language_code = analyze_dict['language']
    language = settings.LANGUAGE_MAPPING[language_code]
    map_token_pos_to_level(language_code)
    analyzed_text = analyze_dict['text']
    summary = analyze_dict['summary']
    obj_type_label = obj_type_label_dict.get(obj_type, _('text corpus'))
    var_dict = { 'obj_type': obj_type, 'obj_id': obj_id, 'description': description, 'title': title, 'obj_type_label': obj_type_label, 'language_code': language_code, 'language': language, 'text': body or analyzed_text, 'analyzed_text': analyzed_text, 'summary': summary }
    if summarization:
        return var_dict
    if nounchunks:
        ncs = analyze_dict['noun_chunks']
        noun_chunks = []
        for nc in ncs:
            nc = nc.replace('\n', ' ').replace('\xa0', ' ')
            tokens = nc.split()
            if len(tokens)>1:
                noun_chunks.append(' '.join(tokens))
        noun_chunks = [nc for nc in noun_chunks if len(nc.split())>1]
        var_dict['noun_chunks'] = noun_chunks
        return var_dict
    text = analyze_dict['text']
    sentences = analyze_dict['sents']
    var_dict['n_sentences'] = n_sentences = len(sentences)
    tokens = analyze_dict['tokens']
    var_dict['n_tokens'] = n_tokens = len(tokens)
    ents = analyze_dict.get('ents', [])

    kw_frequencies = defaultdict(int)
    adjective_frequencies = defaultdict(int)
    noun_frequencies = defaultdict(int)
    propn_frequencies = defaultdict(int)
    verb_frequencies = defaultdict(int)
    adverb_frequencies = defaultdict(int)
    cconj_frequencies = defaultdict(int)
    sconj_frequencies = defaultdict(int)
    n_lexical = 0
    if readability:
        n_words = 0
        n_hard_words = 0
        n_word_characters = 0
        n_word_syllables = 0
    for item in tokens:
        token = text[item['start']:item['end']]
        item['text'] = token 
        pos = item['pos']
        if readability: # and not pos in ['SPACE', 'PUNCT',]:
            n_words += 1
            word_characters = len(token)
            n_word_characters += word_characters
            word_syllables = count_word_syllables(token, language_code)
            n_word_syllables += word_syllables
            if word_syllables > 2:
                n_hard_words += 1
        if pos in ['NOUN', 'PROPN', 'VERB', 'ADJ', 'ADV',]:
            n_lexical += 1
        lemma = item['lemma']
        if wordlists:
            if pos == 'CCONJ':
                add_to_default_dict(cconj_frequencies, lemma)
            elif pos == 'SCONJ':
                add_to_default_dict(sconj_frequencies, lemma)
        if token.isnumeric() or pos in EMPTY_POS or item['stop']:
            continue
        # n_lexical += 1
        add_to_default_dict(kw_frequencies, token)
        if pos in ['NOUN',]:
            add_to_default_dict(noun_frequencies, lemma)
        elif pos == 'VERB':
            add_to_default_dict(verb_frequencies, lemma)
        elif pos == 'ADJ':
            add_to_default_dict(adjective_frequencies, lemma)
        elif wordlists:
            if pos == 'PROPN':
                add_to_default_dict(propn_frequencies, lemma)
            elif pos == 'ADV':
                add_to_default_dict(adverb_frequencies, lemma)
    if readability:
        var_dict['n_words'] = n_words
        var_dict['n_hard_words'] = n_hard_words
        var_dict['n_word_characters'] = n_word_characters
        var_dict['n_word_syllables'] = n_word_syllables
    n_unique = len(kw_frequencies)
    voc_density = n_tokens and n_unique/n_tokens or 0
    lex_density = n_tokens and n_lexical/n_tokens or 0
    kw_frequencies = sorted_frequencies(kw_frequencies)
    verb_frequencies = sorted_frequencies(verb_frequencies)
    noun_frequencies = sorted_frequencies(noun_frequencies)
    adjective_frequencies = sorted_frequencies(adjective_frequencies)
    adverb_frequencies = sorted_frequencies(adverb_frequencies)
    if wordlists:
        propn_frequencies = sorted_frequencies(propn_frequencies)
        cconj_frequencies = sorted_frequencies(cconj_frequencies)
        sconj_frequencies = sorted_frequencies(sconj_frequencies)
        var_dict.update({'propn_frequencies': propn_frequencies,
            'cconj_frequencies': cconj_frequencies, 'sconj_frequencies': sconj_frequencies,})
    if token_level_dict:
        levels_counts = defaultdict(int)
        lc_dict = add_level_to_frequencies(verb_frequencies, 'verb')
        for item in lc_dict.items():
            levels_counts[item[0]] += item[1]
        lc_dict = add_level_to_frequencies(noun_frequencies, 'noun')
        for item in lc_dict.items():
            levels_counts[item[0]] += item[1]
        lc_dict = add_level_to_frequencies(adjective_frequencies, 'adjective')
        for item in lc_dict.items():
            levels_counts[item[0]] += item[1]
        lc_dict = add_level_to_frequencies(adverb_frequencies, 'adverb')
        for item in lc_dict.items():
            levels_counts[item[0]] += item[1]

    var_dict.update({'verb_frequencies': verb_frequencies, 'noun_frequencies': noun_frequencies,
        'adjective_frequencies': adjective_frequencies, 'adverb_frequencies': adverb_frequencies,
        'levels_counts': levels_counts,})
    if wordlists and not readability:
        return var_dict

    mean_sentence_length = n_tokens/n_sentences
    index_sentences(sentences, tokens)
    max_sentence_length = 0
    max_dependency_depth = 0
    tot_dependency_depth = 0
    max_dependency_distance = 0
    tot_dependency_distance = 0
    max_weighted_distance = 0
    tot_weighted_distance = 0
    for sentence in sentences:
        sentence_length = make_sentence_tree(sentence, tokens)
        max_sentence_length = max(max_sentence_length, sentence_length)
        depth = sentence_dependency_depth(sentence, tokens)
        max_dependency_depth = max(max_dependency_depth, depth)
        tot_dependency_depth += depth
        distance = sentence_dependency_distance(sentence, tokens)
        max_dependency_distance = max(max_dependency_distance, distance)
        tot_dependency_distance += distance
        weighted_distance = distance / sentence_length
        max_weighted_distance = max(max_weighted_distance, weighted_distance)
        tot_weighted_distance += weighted_distance
    mean_dependency_depth = n_sentences and (tot_dependency_depth / n_sentences) or 0
    mean_dependency_distance = n_sentences and (tot_dependency_distance / n_sentences) or 0
    mean_weighted_distance = n_sentences and (tot_weighted_distance / n_sentences) or 0

    entitiy_dict = defaultdict(list)
    index_entities(ents, tokens, entitiy_dict)
    entity_lists = [{'key': key, 'entities': entities} for key, entities in entitiy_dict.items()]

    var_dict.update({'n_unique': n_unique, 'voc_density': voc_density, 'lex_density': lex_density,
                     'mean_sentence_length': mean_sentence_length, 'max_sentence_length': max_sentence_length,
                     'max_dependency_depth': max_dependency_depth, 'mean_dependency_depth': mean_dependency_depth,
                     'max_dependency_distance': max_dependency_distance, 'mean_dependency_distance': mean_dependency_distance,
                     'max_weighted_distance': max_weighted_distance, 'mean_weighted_distance': mean_weighted_distance,
                     'sentences': sentences, 'tokens': tokens,
                     'kw_frequencies': kw_frequencies[:16],
                     'entity_lists': entity_lists, 'entities': ents,
                     'collData': collData, 'docData': docData,
                     })
    return text_dashboard_return(request, var_dict)

def brat(request):
    return render(request, 'vue/brat.html', {})

TEXT_MIMETYPE_KEYS = (
  'text',
  'pdf',
  'rtf',
  'msword',
  'wordprocessingml.document',
  'officedocument.wordprocessingml',
)

def propagate_remote_server_error(response):
    ajax_response = JsonResponse({"error": "Remote server error"})
    ajax_response.status_code = response.status_code
    return ajax_response

@csrf_exempt
def ajax_new_corpus(request):
    user_key = '{id:05d}'.format(id=request.user.id)
    endpoint = nlp_url + '/api/new_corpus/'
    data = json.dumps({'user_key': user_key})
    response = requests.post(endpoint, data=data)
    if not response.status_code==200:
        return propagate_remote_server_error(response)
    data = response.json()
    file_key = data['file_key']
    result = {'file_key': file_key}
    return JsonResponse(result)

@csrf_exempt
def ajax_insert_item(request):
    data = json.loads(request.body.decode('utf-8'))
    file_key = data['file_key']
    index = data['index']
    item = data['item']
    obj_type = item['obj_type']
    obj_id = item['obj_id']
    url = item['url']
    from commons import text_utils
    title, description, text = text_utils.get_obj_text(None, obj_type=obj_type, obj_id=obj_id, return_has_text=False, with_children=True)
    text = ". ".join([title, description, text])
    data = json.dumps({'file_key': file_key, 'index': index, 'obj_type': obj_type, 'obj_id': obj_id, 'label': title, 'url': url, 'text': text})
    endpoint = nlp_url + '/api/add_doc/'
    response = requests.post(endpoint, data=data)
    if not response.status_code==200:
        return propagate_remote_server_error(response)
    data = response.json()
    file_key = data['file_key']
    if file_key:
        result = {'file_key': file_key, 'index': index, 'language': data['language'], 'n_tokens': data['n_tokens'], 'n_words': data['n_words']}
    else:
        result = {'file_key': file_key, 'error': 'languages cannot be mixed in corpus'}
    return JsonResponse(result)

"""
called from contents_dashboard template to remove an item (doc) from a corpus (docbin)
"""
@csrf_exempt
def ajax_remove_item(request):
    endpoint = nlp_url + '/api/remove_doc/'
    data = json.loads(request.body.decode('utf-8'))
    file_key = data['file_key']
    obj_type = data['obj_type']
    obj_id = data['obj_id']
    data = json.dumps({'file_key': file_key, 'obj_type': obj_type, 'obj_id': obj_id})
    response = requests.post(endpoint, data=data)
    if response.status_code==200:
        data = response.json()
        index = data['index']
        result = {'index': index}
        return JsonResponse(result)
    else:
        return propagate_remote_server_error(response)

"""
called from contents_dashboard template to make a corpus of a list of resources
and return summary information on the application of the spaCy pipleline
"""
@csrf_exempt
def ajax_make_corpus(request):
    data = json.loads(request.body.decode('utf-8'))
    resources = data['items']
    user_key = '{id:05d}'.format(id=request.user.id)
    file_key = ''
    endpoint = nlp_url + '/api/add_doc/'
    processed = []
    for resource in resources:
        obj_type = resource['obj_type']
        obj_id = resource['obj_id']
        url = resource['url']
        from commons import text_utils
        title, description, text = text_utils.get_obj_text(None, obj_type=obj_type, obj_id=obj_id, return_has_text=False, with_children=True)
        text = ". ".join([title, description, text])
        data = json.dumps({'file_key': file_key, 'user_key': user_key, 'obj_type': obj_type, 'obj_id': obj_id, 'label': title, 'url': url, 'text': text})
        response = requests.post(endpoint, data=data)
        if not response.status_code==200:
            return propagate_remote_server_error(response)
        data = response.json()
        file_key = data['file_key']
        data.update({'obj_type': obj_type, 'obj_id': obj_id, 'label': title})
        processed.append(data)
    return JsonResponse({'result': processed, 'file_key': file_key})

"""
called from contents_dashboard template
to list corpora associated to a user or a project
"""
@csrf_exempt
def ajax_get_corpora(request):
    data = json.loads(request.body.decode('utf-8'))
    project_key = data.get('project_key', '')
    if not project_key:
        user_key = '{id:05d}'.format(id=request.user.id)
    endpoint = nlp_url + '/api/get_corpora/'
    data = json.dumps({'user_key': user_key, 'project_key': project_key})
    response = requests.post(endpoint, data=data)
    if response.status_code==200:
        corpora = response.json()
        return JsonResponse(corpora)
    else:
        return propagate_remote_server_error(response)

"""
called from contents_dashboard template
to delete an entire corpus (docbin)
"""
@csrf_exempt
def ajax_delete_corpus(request):
    endpoint = nlp_url + '/api/delete_corpus/'
    data = json.loads(request.body.decode('utf-8'))
    file_key = data['file_key']
    data = json.dumps({'file_key': file_key})
    response = requests.post(endpoint, data=data)
    if response.status_code==200:
        result = response.json()
        file_key = result['file_key']
        data = {'file_key': file_key}
        return JsonResponse(data)
    else:
        return propagate_remote_server_error(response)

@csrf_exempt
def text_wordlists(request, file_key='', obj_type='', obj_id=''):
    var_dict = {'file_key': file_key, 'obj_type': obj_type, 'obj_id': obj_id}
    # if request.is_ajax():
    if is_ajax(request):
        keys = ['verb_frequencies', 'noun_frequencies', 'adjective_frequencies', 'adverb_frequencies', 
                'propn_frequencies', 'cconj_frequencies', 'sconj_frequencies',
                'obj_type_label', 'title', 'language']
        data = var_dict
        dashboard_dict = text_dashboard(request, file_key=file_key, obj_type=obj_type, obj_id=obj_id, wordlists=True)
        data.update([[key, dashboard_dict[key]] for key in keys])
        return JsonResponse(data)
    else:
        return render(request, 'vue/text_wordlists.html', var_dict)

"""
called from contents_dashboard or text_analysis template
to find and sort document or corpus keywords and to list keyword in context
"""
@csrf_exempt
def context_dashboard(request, file_key='', obj_type='', obj_id=''):
    var_dict = {'file_key': file_key, 'obj_type': obj_type, 'obj_id': obj_id}
    # if request.is_ajax():
    if is_ajax(request):
        var_dict = text_dashboard(request, file_key=file_key, obj_type=obj_type, obj_id=obj_id, contexts=True)
        endpoint = nlp_url + '/api/word_contexts/'
        data = json.dumps(var_dict)
        response = requests.post(endpoint, data=data)
        result = response.json()
        var_dict['language'] = result['language']
        var_dict['keywords'] = result['keywords']
        var_dict['kwics'] = result['kwics']
        return JsonResponse(var_dict)
    else:
        return render(request, 'vue/context_dashboard.html', var_dict)

def text_summarization(request, params):
    var_dict = text_dashboard(request, obj_type=params['obj_type'], obj_id=params['obj_id'], file_key=params['file_key'], summarization=True)
    error = var_dict.get('error', None)
    if error:
        print('error:', error)
    else:
        # var_dict.update(params)
        pass
    return render(request, 'text_summarization.html', var_dict)

"""
def text_nounchunks(request, params={}):
    var_dict = text_dashboard(request, 'text', 0, nounchunks=True)
"""
def text_nounchunks(request, params):
    var_dict = text_dashboard(request, obj_type=params['obj_type'], obj_id=params['obj_id'], file_key=params['file_key'], nounchunks=True)
    error = var_dict.get('error', None)
    if error:
        print('error:', error)
    else:
        var_dict.update(params)
    language_code = var_dict['language_code']
    return render(request, 'text_nounchunks.html', var_dict)

readability_indexes = {
  'flesch_easy': { 'languages': ['en'], 'title': "Flesch Reading Ease score for English (0-100)", 'ref': 'https://en.wikipedia.org/wiki/Flesch%E2%80%93Kincaid_readability_tests' },
  'franchina_vacca_1972': { 'languages': ['it'], 'title': "Franchina-Vacca readability index for Italian (0-100)", 'ref': 'https://it.wikipedia.org/wiki/Formula_di_Flesch' },
  'gulp_ease': { 'languages': ['it'], 'title': "GULP readability index for Italian (0-100)", 'ref': 'https://it.wikipedia.org/wiki/Indice_Gulpease' },
  'kincaid_flesh': { 'languages': ['en'], 'title': "Flesch–Kincaid grade level for English (Very easy-Extra difficult)", 'ref': 'https://en.wikipedia.org/wiki/Flesch%E2%80%93Kincaid_readability_tests' },
  'fernandez_huerta': { 'languages': ['es'], 'title': "Fernandez Huerta readability index for Spanish (0-100)", 'ref': 'https://legible.es/blog/lecturabilidad-fernandez-huerta/' },
  'gagatsis_1985': { 'languages': ['el'], 'title': "Gagatsis readability index for Greek (0-100)", 'ref': 'http://www.sfs.uni-tuebingen.de/~dm/papers/Georgatou-16.pdf' },
}
# gagatsis_1985. see: http://www.sfs.uni-tuebingen.de/~dm/papers/Georgatou-16.pdf

readability_scales = {
    'flesch_easy': [[90, 100, 'very easy'], [80, 90, 'easy'], [70, 80, 'fairly easy'], [60, 70, 'intermediate'], [50, 60, 'fairly difficult'], [30, 50, 'difficult'], [0, 30, 'very difficult'],],
    'kincaid_flesh': [[90, 100, '5th grade'], [80, 90, '6th grade'], [70, 80, '7th grade'], [60, 70, '8-9th grade'], [50, 60, '10-12 grade'], [30, 50, 'college'], [10, 30, 'college graduate'], [0, 10, 'professional'],]
}

def readability_level(scale, score):
    score = int(score)
    scale = readability_scales[scale]
    for interval in scale:
        if score >= interval[0] and score <= interval[1]:
            return interval[2]
    return 'out of scale'

level_rarity_factors = {
  'a': 0.1,
  'a1': 0.0,
  'a2': 0.2,
  'b': 0.4,
  'b1': 0.3,
  'b2': 0.5,
  'c': 0.7,
  'c1': 0.6,
  'c2': 1.0,
}

def compute_lexical_rarity(levels_counts):
    total_count = 0
    absolute_rarity = 0
    for level, count in levels_counts.items():
        total_count += count
        absolute_rarity += count*level_rarity_factors[level]
    return total_count and absolute_rarity/total_count or 0

"""
def text_readability(request, params={}):
    var_dict = text_dashboard(request, 'text', 0, readability=True)
    error = var_dict.get('error', None)
"""
def text_readability(request, params):
    var_dict = text_dashboard(request, obj_type=params['obj_type'], obj_id=params['obj_id'], file_key=params['file_key'], readability=True)
    error = var_dict.get('error', None)
    if error:
        print('error:', error)
    else:
        var_dict.update(params)
    language_code = var_dict['language_code']
    n_tokens = var_dict['n_tokens'] or 1
    n_words = var_dict['n_words'] or 1
    var_dict['mean_chars_per_word'] = var_dict['n_word_characters'] / n_words
    var_dict['mean_syllables_per_word'] = var_dict['n_word_syllables'] / n_words
    var_dict['lexical_rarity'] = compute_lexical_rarity(var_dict['levels_counts']) 
    var_dict['readability_indexes'] = {}
    index = readability_indexes['flesch_easy']
    if language_code in index['languages']:
        index['value'] = 206.835 - 1.015 * var_dict['mean_sentence_length'] - 84.6 * var_dict['mean_syllables_per_word']
        index['range'] = readability_level('flesch_easy', index['value'])
        var_dict['readability_indexes']['flesch_easy'] = index
    index = readability_indexes['kincaid_flesh']
    if language_code in index['languages']:
        index['value'] = 0.39 * var_dict['mean_sentence_length'] + 11.8 * var_dict['mean_syllables_per_word'] - 15.59
        index['range'] = readability_level('kincaid_flesh', index['value'])
        var_dict['readability_indexes']['kincaid_flesh'] = index
    index = readability_indexes['franchina_vacca_1972']
    if language_code in index['languages']:
        index['value'] = 206 - var_dict['mean_sentence_length'] - 65 * var_dict['mean_syllables_per_word']
        index['range'] = readability_level('flesch_easy', index['value'])
        var_dict['readability_indexes']['franchina_vacca_1972'] = index
    index = readability_indexes['gulp_ease']
    if language_code in index['languages']:
        index['value'] = 89 - 10 * var_dict['mean_chars_per_word'] + 100 * var_dict['n_sentences'] / n_words
        index['range'] = readability_level('flesch_easy', index['value'])
        var_dict['readability_indexes']['gulp_ease'] = index
    index = readability_indexes['fernandez_huerta']
    if language_code in index['languages']:
        index['value'] = 206.84 - 1.02 * var_dict['mean_sentence_length'] - 60 * var_dict['mean_syllables_per_word']
        index['range'] = readability_level('flesch_easy', index['value'])
        var_dict['readability_indexes']['gulp_ease'] = index
    index = readability_indexes['gagatsis_1985']
    if language_code in index['languages']:
        index['value'] = 206.835 - 1.015 * var_dict['mean_sentence_length'] - 59 * var_dict['mean_syllables_per_word']
        index['range'] = readability_level('flesch_easy', index['value'])
        var_dict['readability_indexes']['gagatsis_1985'] = index
    return render(request, 'text_readability.html', var_dict)

def text_analysis_input(request):
    var_dict = {}
    if request.POST:
        form = TextAnalysisInputForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            function = data['function']
            request.session['text'] = data['text']
            # return text_analyze(request, function, 'text', 0)
            if function == 'dashboard': # Text Analysis Dashboard
                var_dict = {'obj_type': 'text', 'obj_id': 0}
                return render(request, 'vue/text_dashboard.html', var_dict)
            else:
                # return text_analyze(request, function, 'text', 0)
                return text_analyze(request, function, obj_type='text', obj_id=0)
    else:
        # do not present the input form if the language server is down
        endpoint = nlp_url + '/api/configuration'
        response = None
        try:
            response = requests.get(endpoint)
        except:
            print(response.status_code)
        if response and response.status_code == 200:
            var_dict = response.json()
            form = TextAnalysisInputForm()
            var_dict['form'] = form
        else:
            var_dict['error'] = off_error
    return render(request, 'text_analysis_input.html', var_dict)

# def text_analyze(request, function, obj_type, obj_id, file_key='', text=''):
def text_analyze(request, function, obj_type='', obj_id='', file_key='', text=''):
    var_dict = { 'obj_type': obj_type, 'obj_id': obj_id, 'file_key': file_key, 'title': '' }
    if file_key:
        if obj_type == 'corpus':
            var_dict['obj_type'] = ''
    else:
        var_dict['obj_type_label'] = obj_type_label_dict[obj_type]
        if obj_type == 'text':
                var_dict['obj_id'] = 0
    if function == 'dashboard':
        return render(request, 'vue/text_dashboard.html', var_dict)
    elif function == 'context':
        var_dict['VUE'] = True
        return render(request, 'vue/context_dashboard.html', var_dict)
    elif function == 'summarization':
        var_dict['VUE'] = True
        return text_summarization(request, params=var_dict)
    elif function == 'readability':
        var_dict['VUE'] = True
        return text_readability(request, params=var_dict)
    elif function == 'nounchunks':
        var_dict['VUE'] = True
        return text_nounchunks(request, params=var_dict)
    elif function == 'wordlists':
        var_dict['VUE'] = True
        return render(request, 'vue/text_wordlists.html', var_dict)
