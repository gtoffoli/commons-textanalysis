from importlib import import_module
import math
import json
import requests
import hashlib
from collections import defaultdict, OrderedDict
from operator import itemgetter

from django.http import HttpRequest, HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.text import capfirst
from django.views.decorators.csrf import csrf_exempt
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.models import User

from commons.models import Document, OER
from commons.models import is_site_member
from commons.models import DRAFT, RESTRICTED, PUBLISHED, PUBLICATION_STATE_DICT
from commons.user_spaces import project_contents, user_contents

from textanalysis.forms import TextAnalysisInputForm
from textanalysis.readability import readability_indexes, readability_indexes_keys, readability_level
from textanalysis.readability import compute_lexical_rarity, cs_readability_01
from textanalysis.babelnet import bn_domains, BN_slugify, BN_format
from textanalysis.utils import get_file_text, get_web_resource_text, is_ajax
from textanalysis.utils import add_to_default_dict, MATTR, lemmas_to_colors
from textanalysis.utils import LemmaPosDict
from textanalysis.utils import GenericSyllabizer
from textanalysis.utils import DEFAULT_ENTITY_COLOR, DEFAULT_LABEL_COLORS
from textanalysis.utils import read_input_file, load_corpus_metadata, save_corpus_metadata, rename_corpus_metadata
from textanalysis.tbx import tbx_xml_2_dict, tbx_languages, tbx_subjects, tbx_filter_by_language

if settings.DEBUG:
    nlp_url = 'http://localhost:8001'
else:
    nlp_url = settings.NLP_URL

obj_type_label_dict = {
    'project': _('commonspaces project'),
    'doc': _('document file'),
    'drive': _('google document'),
    'oer': _('open educational resource'),
    'pathnode': _('node of learning path'),
    'lp': _('learning path'),
    'web': _('remote web resource'),
    'text': _('manually input text'),
    'corpus': _('text corpus'),
    '': '?',
}

# from: https://sashamaps.net/docs/resources/20-colors/
distinct_colors = [
  ['Red', '#e6194b'], ['Green', '#3cb44b'], ['Yellow', '#ffe119'], ['Blue', '#4363d8'], ['Orange', '#f58231'],
  ['Purple', '#911eb4'], ['Cyan', '#46f0f0'], ['Magenta', '#f032e6'], ['Lime', '#bcf60c'], ['Pink', '#fabebe'],
  ['Teal', '#008080'], ['Lavender', '#e6beff'], ['Brown', '#9a6324'], ['Beige', '#fffac8'], ['Maroon', '#800000'],
  ['Mint', '#aaffc3'], ['Olive', '#808000'], ['Apricot', '#ffd8b1'], ['Navy', '#000075'], ['Grey', '#808080'],
  ['White', '#ffffff'], ['Black', '#000000'],
]
color_dict = dict(distinct_colors)
color_list = [color_name for color_name, color_code in distinct_colors]

pos_table = (
    ('PROPN', {'label': 'proper noun', 'color': 'Magenta', 'selected': 1,},),
    ('DET', {'label': 'determiner', 'color': 'Lime', 'selected': 0,},),
    ('NOUN', {'label': 'noun', 'color': 'Red', 'selected': 1,},),
    ('PRON', {'label': 'pronoun', 'color': 'Orange', 'selected': 0,},),
    ('ADJ', {'label': 'adjective', 'color': 'Green', 'selected': 1,},),
    ('NUM', {'label': 'numeral', 'color': 'Mint', 'selected': 0,},),
    ('AUX', {'label': 'auxiliary verb', 'color': 'Blue', 'selected': 0,},),
    ('VERB', {'label': 'verb', 'color': 'Navy', 'selected': 1,},),
    ('ADV', {'label': 'adverb', 'color': 'Teal', 'selected': 1,},),
    ('ADP', {'label': 'adposition', 'color': 'Grey', 'selected': 0,},),
    ('CCONJ', {'label': 'coordinating conjunction', 'color': 'Brown', 'selected': 0,},),
    ('SCONJ', {'label': 'subordinating conjunction', 'color': 'Maroon', 'selected': 0,},),
)
pos_map = dict(pos_table)
pos_list = [pos[0] for pos in pos_table]

ENTITY_TYPES = ['PER', 'LOC', 'GPE', 'ORG'] # , 'PERSON', 'DERIV_PER'

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

postag_color = 'CornflowerBlue'
entity_color = 'White'
dependency_color = 'Purple'
nounchunk_color = 'LightGrey' # "#ff9561", 'Yellow' #'Khaki' # 'LightSalmon' # 'Tomato' # 'Coral' 
term_color = 'White'
"""
# from NLPBuddy
ENTITIES_MAPPING = {
    'PER': _('person'),
    'LOC': _('other location'),
    'GPE': _('GPE location'),
    'ORG': _('organization'),
    'MISC': _('miscellaneous'),
}
"""
# ===== froom BRAT; see http://brat.nlplab.org/configuration.html and https://brat.nlplab.org/embed.html
collData = {
    'entity_types': [
        { 'type': 'ADJ', 'labels': ['noun chunk', 'nchunk'], 'bgColor': nounchunk_color, 'borderColor': 'darken' },

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

        { 'type': 'PER', 'labels': ['Person entity', 'Per'], 'bgColor': entity_color, 'borderColor': 'darken' }, # People, including fictional.
        { 'type': 'PERSON', 'labels': ['Person entity', 'Per'], 'bgColor': entity_color, 'borderColor': 'darken' }, # People, including fictional.
        # { 'type': 'DERIV_PER', 'labels': ['Derivative person entity', 'Per'], 'bgColor': entity_color, 'borderColor': 'darken' }, # People, including fictional.
        { 'type': 'NORP', 'labels': ['NORP', 'NORP'], 'bgColor': entity_color, 'borderColor': 'darken' },  # Nationalities or religious or political groups.
        { 'type': 'FAC', 'labels': ['Facility', 'Fac'], 'bgColor': entity_color, 'borderColor': 'darken' }, # Buildings, airports, highways, bridges, etc.
        { 'type': 'ORG', 'labels': ['Organization entity', 'Org'], 'bgColor': entity_color, 'borderColor': 'darken' }, # Companies, agencies, institutions, etc.
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
        { 'type': 'MISC', 'labels': ['Miscellaneous entity', 'Mix'], 'bgColor': entity_color, 'borderColor': 'darken' }, # Numerals that do not fall under another type.
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

entity_dict = {}
for item in collData['entity_types']:
    entity_type = item['type'].upper()
    entity_dict[entity_type] = {'label': item['labels'][0], 'count': 0}
 
default_entity_types = ['PER','ORG','GPE', 'LOC',]
span_type_buttons = {
    'nounchunk': {'selected': False, 'label': capfirst(_("noun chunks")), 'border': 'black', 'background': nounchunk_color,},
    'glossary': {'selected': True, 'label': capfirst(_("glossary terms")), 'border': 'lightseagreen', 'background': term_color,},
    'babelnet': {'selected': True, 'label': capfirst(_("babenet synsets")), 'border': 'blue', 'background': term_color,},
}

def define_span_types():
    entity_types = []
    for item in collData['entity_types']:
        entity_type = item['type'].upper()
        if not entity_dict.get(entity_type, None):
            continue
        if entity_dict[entity_type]['count']:
            entity_types.append(entity_type)
            span_type_buttons[entity_type] = {}
            span_type_buttons[entity_type]['label'] = entity_dict[entity_type]['label']
            span_type_buttons[entity_type]['background'] = entity_color
            span_type_buttons[entity_type]['border'] = DEFAULT_LABEL_COLORS.get(entity_type, DEFAULT_ENTITY_COLOR)
            if entity_type in default_entity_types:
                span_type_buttons[entity_type]['selected'] = True
    span_type_buttons['n'] = {'selected': False} # null entity
    return  entity_types + ['nounchunk'] + ['glossary', 'babelnet',]

def count_word_syllables(word, language_code):
    n_chars = len(word)
    word = word + '  '
    n_syllables = 0
    if language_code == 'en': # see: https://medium.com/@mholtzscher/programmatically-counting-syllables-ca760435fab4
        from textanalysis.lang.en.utils import count_word_syllables as count_word_syllables_en
        n_syllables = count_word_syllables_en(word)
    elif language_code == 'it': # see: https://it.comp.programmare.narkive.com/TExPlcuC/programma-di-sillabazione
        from textanalysis.lang.it.utils import count_word_syllables as count_word_syllables_it
        n_syllables = count_word_syllables_it(word)
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
    n_tokens = len(tokens)
    for ent in ents:
        label = ent['label']
        start = ent['start']
        end = ent['end']
        while tokens[i]['start'] < start:
            i += 1
        assert start==tokens[i]['start']
        ent['start_token'] = i
        text = ''
        while i <n_tokens and tokens[i]['end'] <= end:
            text += tokens[i]['text']
            i += 1
        ent['end_token'] = i
        ent['text'] = text
        if not '_' in text and not text in entity_dict[label]:
            entity_dict[label].append(text)

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

def token_to_level(token, frequencies):
    pos = token['pos']
    lemma = token['lemma']
    item = frequencies.get(lemma, None)
    return item and item[1] or '?'

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

def sorted_frequencies(d):
    sd =  OrderedDict(sorted(d.items(), key = itemgetter(1), reverse = True))
    return [{'key': key, 'freq': freq} for key, freq in sd.items()]

def add_level_to_frequencies(frequencies, pos):
    """ as a side-effect, replace the frequency in each dict item with a tuple [frequency, level];
        return a dict of levels frequencies """
    level_count_dict = defaultdict(int)
    for lemma, frequency in frequencies.items():
        key = '_'.join([lemma.lower(), pos])
        level = token_level_dict.get(key, 'c2')
        frequencies[lemma] = [frequency, level]
        level_count_dict[level] += frequency
    return level_count_dict

def getter_1_0(item):
    return item[1][0]

def sorted_frequencies_with_levels(d):
    sd =  OrderedDict(sorted(d.items(), key = getter_1_0, reverse = True))
    return [{'key': key, 'freq': freq_level[0], 'level': freq_level[1], freq_level[1][0]: True} for key, freq_level in sd.items()]

def text_dashboard_return(request, var_dict):
    if not var_dict:
        var_dict = { 'error': off_error }
    if is_ajax(request):
        return JsonResponse(var_dict)
    else:
        return var_dict # only for manual test

@csrf_exempt
def text_dashboard(request, obj_type='', obj_id='', file_key='', label='', url='', tbx_dict=None, obj=None, title='', body='',
       wordlists=False, readability=False, analyzed_text=False, nounchunks=False, contexts=False, summarization=False, text_annotation=False, text_cohesion=False, dependency=False, glossaries=[], domains=[]):
    """ here (originally only) through ajax call from the template 'vue/text_dashboard.html' """
    if readability:
        wordlists = True
    if not file_key and not obj_type in ['project', 'oer', 'lp', 'pathnode', 'doc', 'drive', 'flatpage', 'web', 'text',]:
        return HttpResponseForbidden()
    description = ''
    if file_key:
        data = {'file_key': file_key, 'obj_type': obj_type, 'obj_id': obj_id}
        if nounchunks:
            data['glossaries'] = glossaries
            data['domains'] = domains
    else:
        if obj_type == 'text':
            title, description, body = ['', '', request.session.get('text', '')]
        elif obj_type == 'web':
            title, body, response, err = get_web_resource_text(url)
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
            return {'text': body, 'title': title}
        data = {'text': body}
    if tbx_dict:
        data['glossary'] = glossary_filter_terms(tbx_dict)
    data = json.dumps(data)
    if text_cohesion:
        endpoint = nlp_url + '/api/text_cohesion'
    else:
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
    doc = analyze_dict['doc']
    language_code = analyze_dict['language']
    language = settings.LANGUAGE_MAPPING[language_code]
    map_token_pos_to_level(language_code)
    if file_key:
        text = doc.get('text', '')
        label = doc['_'].get('label', '')
        url = doc['_'].get('url', '')
    analyzed_text = analyze_dict.get('analyzed_text', '')
    obj_type_label = obj_type_label_dict.get(obj_type, _('text corpus'))
    var_dict = { 'obj_type': obj_type, 'obj_id': obj_id, 'description': description, 'title': title, 'label': label, 'url': url, 'obj_type_label': obj_type_label, 'language_code': language_code, 'language': language, 'text': body or text, 'analyzed_text': analyzed_text }
    var_dict['summary'] = analyze_dict.get('summary', '')

    text = analyze_dict['doc']['text']
    sentences = analyze_dict['doc']['sents']
    var_dict['n_sentences'] = n_sentences = len(sentences)
    tokens = analyze_dict['doc']['tokens']
    var_dict['tokens'] = tokens
    var_dict['n_tokens'] = n_tokens = len(tokens)
    var_dict['mean_sentence_length'] = mean_sentence_length = n_tokens/n_sentences
    entities = analyze_dict['doc']['ents']
    var_dict['entities'] = entities
    entitiy_dict = defaultdict(list)
    index_entities(entities, tokens, entitiy_dict)
    entity_lists = [{'key': key, 'entities': entities} for key, entities in entitiy_dict.items()]
    var_dict['entity_lists'] = entity_lists,

    if summarization:
        return var_dict

    if text_annotation:
        for k in ['doc', 'paragraphs',]:
            var_dict[k] = analyze_dict[k]
        return var_dict       

    if text_cohesion:
        for k in ['doc', 'paragraphs', 'repeated_lemmas', 'cohesion_by_similarity', 'cohesion_by_repetitions', 'cohesion_by_entity_graph']:
            var_dict[k] = analyze_dict[k]
        return var_dict

    pos_frequencies = defaultdict(int)
    kw_frequencies = defaultdict(int)
    adjective_frequencies = defaultdict(int)
    noun_frequencies = defaultdict(int)
    propn_frequencies = defaultdict(int)
    verb_frequencies = defaultdict(int)
    adverb_frequencies = defaultdict(int)
    cconj_frequencies = defaultdict(int)
    sconj_frequencies = defaultdict(int)
    n_lexical = 0
    n_long_tokens = 0
    if readability:
        mattr = MATTR(text, tokens)
        n_words = 0
        n_hard_words = 0
        n_word_characters = 0
        n_word_syllables = 0
    for token in tokens:
        token_text = text[token['start']:token['end']]
        token['text'] = token_text 
        if len(token_text) > 6:
            n_long_tokens += 1
        pos = token['pos']
        pos_frequencies[pos] += 1
        add_to_default_dict(kw_frequencies, token_text)
        if readability: # and not pos in ['SPACE', 'PUNCT',]:
            mattr.add_token()
            n_words += 1
            word_characters = len(token_text)
            n_word_characters += word_characters
            word_syllables = count_word_syllables(token_text, language_code)
            n_word_syllables += word_syllables
            if word_syllables > 2:
                n_hard_words += 1
        if pos in ['NOUN', 'PROPN', 'VERB', 'ADJ', 'ADV',]:
            n_lexical += 1
        lemma = token['lemma']
        if wordlists:
            if pos == 'CCONJ':
                add_to_default_dict(cconj_frequencies, lemma)
            elif pos == 'SCONJ':
                add_to_default_dict(sconj_frequencies, lemma)
        if token_text.isnumeric() or pos in EMPTY_POS or token['stop']:
            continue
        # add_to_default_dict(kw_frequencies, token_text)
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
    n_unique = len(kw_frequencies)
    var_dict['pos_frequencies'] = pos_frequencies
    if readability:
        var_dict['n_words'] = n_words
        var_dict['n_hard_words'] = n_hard_words
        var_dict['n_word_characters'] = n_word_characters
        var_dict['n_word_syllables'] = n_word_syllables
        voc_density = mattr.get_average()
    else:
        voc_density = n_tokens and n_unique/n_tokens or 0
    lex_density = n_tokens and n_lexical/n_tokens or 0
    kw_frequencies = sorted_frequencies(kw_frequencies)
    if wordlists:
        propn_frequencies = sorted_frequencies(propn_frequencies)
        cconj_frequencies = sorted_frequencies(cconj_frequencies)
        sconj_frequencies = sorted_frequencies(sconj_frequencies)
        var_dict.update({'propn_frequencies': propn_frequencies,
            'cconj_frequencies': cconj_frequencies, 'sconj_frequencies': sconj_frequencies,})

    levels_counts = defaultdict(int)
    if token_level_dict:
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

    if nounchunks:
        noun_chunks = analyze_dict['noun_chunks']
        # by default all tokens are outside entity spans and noun_chunk spans
        # for token in tokens:
        for i, token in enumerate(tokens):
            token['iob_ent'] = 'o'
            token['iob_chunk'] = 'o'
            token['iob_term'] = 'o'
            token['ent'] = 'n'
            tokens[i] = token
        # annotate tokens with iob info on position in containing entities
        for i, ent in enumerate(entities):
            entity_type = ent['label']
            if not entity_dict.get(entity_type, None):
                continue
            entity_dict[entity_type]['count'] += 1
            if tokens[ent['end_token']-1]['pos'] in ['PUNCT']:
                ent['end_token'] -= 1
            for k in range(ent['start_token'], ent['end_token']):
                token = tokens[k]
                token['ent'] = entity_type
                iob_ent = ''
                if k == ent['start_token']:
                    iob_ent += 'b'
                if k == ent['end_token']-1:
                    iob_ent += 'e'
                if not iob_ent:
                    iob_ent = 'i'
                token['iob_ent'] = iob_ent           
                tokens[k] = token
        # annotate tokens with info on position in containing noun chunks
        for i, chunk in enumerate(noun_chunks):
            for k in range(chunk[0], chunk[1]):
                token = tokens[k]
                token['chunk'] = i
                iob_chunk = ''
                if k == chunk[0]:
                    iob_chunk += 'b'
                if k == chunk[1]-1:
                    iob_chunk += 'e'
                if not iob_chunk:
                    iob_chunk = 'i'
                token['iob_chunk'] = iob_chunk           
                tokens[k] = token
        var_dict['noun_chunks'] = noun_chunks
        # annotate tokens with babelnet synsets already searched by text and filtered by domain
        bn_terms = []
        if file_key:
            bn_terms = analyze_dict.get('bn_terms', [])
            if bn_terms:
                # from (virtual) lists of tokens per term, derive lists of term indexes per token NO
                # annotate first and last token of each term (could be the same)
                for i, bn_term in enumerate(bn_terms):
                    # filter bn_terms based on vocabulary frequency
                    if bn_term['end']-bn_term['start'] == 1:
                        token = tokens[bn_term['start']]
                        if len(token['text']) < 3:
                            continue
                        pos = token['pos']
                        if pos in ['NOUN', 'ADJ', 'VERB', 'ADV',]:
                            frequencies = \
                                (pos=='NOUN' and noun_frequencies) or \
                                (pos=='ADJ' and adjective_frequencies) or \
                                (pos=='VERB' and verb_frequencies) or \
                                (pos=='ADV' and adverb_frequencies)
                            level = token_to_level(token, frequencies)
                            if level in ['a', 'a1', 'a2', 'b', 'b1',]:
                                continue
                    for k in range(bn_term['start'], bn_term['end']):
                        token_bn_terms = tokens[k].get('bn_terms', [])
                        token_bn_terms.append(i)
                        tokens[k]['bn_terms'] = token_bn_terms
                # remove 1 ref to single-token term from tokens with multiple refs
                for token in tokens:
                    term_refs = token.get('bn_terms', [])
                    if len(term_refs) > 1:
                        for ref in term_refs:
                            bn_term = bn_terms[ref]
                            # if len(bn_term) == 1 and bn_term['start'] == token:
                            if (bn_term['end']-bn_term['start']) == 1 and tokens[bn_term['start']] == token:
                                term_refs = [r for r in term_refs if r != ref]
                                token['bn_terms'] = term_refs
                                break
        var_dict['bn_terms'] = bn_terms
        gl_terms = analyze_dict.get('glossary_matches', [])
        if gl_terms:
            # - glossary_matches are a list of dicts with keys {'concept_id', 'start', 'end'}
            # - in the glossary, multiple terms can be associated to the same concept
            # - matches with glossary terms can overlap inside the text; we don't want overlaps
            # 1. From lists of tokens per term, derive lists of terms per token
            # 2. then, get free of overlaps, by choosing longer matches (NO!)
            for term in gl_terms:
                for k in range(term['start'], term['end']):
                    token_gl_terms = tokens[k].get('gl_terms', [])
                    token_gl_terms.append(term)
                    tokens[k]['gl_terms'] = token_gl_terms
            # add to text tokens iob marks related to matches with glossary terms
            for term in gl_terms:
                for k in range(term['start'], term['end']):
                    token = tokens[k]
                    token['concept'] = term['concept_id']
                    iob_term = ''
                    if k == term['start']:
                        iob_term += 'b'
                    if k == term['end']-1:
                        iob_term += 'e'
                    if not iob_term:
                        iob_term = 'i'
                    token['iob_term'] = iob_term           
                    tokens[k] = token
        var_dict['gl_terms'] = gl_terms

    var_dict['tokens'] = tokens
    var_dict['paragraphs'] = analyze_dict['paragraphs']

    # next 4 code lines must be after BabelNet synsets processing
    # since they modify the structure of the frequencies from dict (key->list) to a list of dicts
    verb_frequencies = sorted_frequencies_with_levels(verb_frequencies)
    noun_frequencies = sorted_frequencies_with_levels(noun_frequencies)
    adjective_frequencies = sorted_frequencies_with_levels(adjective_frequencies)
    adverb_frequencies = sorted_frequencies_with_levels(adverb_frequencies)

    var_dict.update({'verb_frequencies': verb_frequencies, 'noun_frequencies': noun_frequencies,
        'adjective_frequencies': adjective_frequencies, 'adverb_frequencies': adverb_frequencies,
        'levels_counts': levels_counts, 'n_long_tokens': n_long_tokens,})

    if (wordlists or nounchunks) and not readability:
        return var_dict

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

    var_dict.update({'n_unique': n_unique, 'voc_density': voc_density, 'lex_density': lex_density,
                     'mean_sentence_length': mean_sentence_length, 'max_sentence_length': max_sentence_length,
                     'max_dependency_depth': max_dependency_depth, 'mean_dependency_depth': mean_dependency_depth,
                     'max_dependency_distance': max_dependency_distance, 'mean_dependency_distance': mean_dependency_distance,
                     'max_weighted_distance': max_weighted_distance, 'mean_weighted_distance': mean_weighted_distance,
                     'sentences': sentences, 'tokens': tokens,
                     'kw_frequencies': kw_frequencies[:16],
                     'collData': collData, 'docData': docData,
                     })
    if dependency:
        return var_dict

    var_dict['VUE'] = True
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
def ajax_contents(request):
    user = request.user
    data = json.loads(request.body.decode('utf-8'))
    project_id = data['project_id']
    user_key = '{id:05d}'.format(id=request.user.id)
    endpoint = nlp_url + '/api/get_corpora/'
    data = json.dumps({'user_key': ''})
    response = requests.post(endpoint, data=data)
    if not response.status_code==200:
        return propagate_remote_server_error(response)
    data = response.json()
    corpora = []
    for corpus in data['corpora']:
        file_key = corpus['file_key']
        metadata = load_corpus_metadata(file_key)
        if not metadata:
            continue
        corpus.update(metadata)
        site_id = corpus.get('site_id', None)
        username = corpus.get('username', '')
        owner = username and User.objects.get(username=username) or None
        state = corpus.get('state', DRAFT)
        if not (user==owner or state==PUBLISHED or (get_current_site(request).id==site_id and state==RESTRICTED)):
            continue
        corpus['owner'] = owner and owner.get_display_name() or _('anonymous')
        corpus['is_owner'] = owner and owner.id == user.id or False
        corpus['open'] = False
        corpus['manage_domains'] = False
        corpus['manage_glossaries'] = False
        corpora.append(corpus)
    if project_id:
        data = project_contents(project_id)
    else: # if user.is_authenticated:
        data = user_contents(user)
    data['corpora'] = corpora
    data['state_dict'] = PUBLICATION_STATE_DICT
    data['sorted_states'] = [1, 5, 3]
    all_glossaries = get_all_glossaries(request).order_by('title')
    data['all_glossaries'] = dict([[glossary.id, glossary.title] for glossary in all_glossaries])
    data['all_domains'] = [BN_format(domain) for domain in bn_domains]
    return JsonResponse(data)

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
    site_id = get_current_site(request).id
    metadata = {'site_id': site_id, 'username': request.user.username, 'state': DRAFT, 'glossaries': [], 'domains': []}
    save_corpus_metadata(file_key, metadata)
    result = {'file_key': file_key}
    return JsonResponse(result)

def add_item_to_corpus(request, file_key, result):
    glossary_ids = load_corpus_metadata(file_key).get('glossaries', [])
    if glossary_ids:
        glossary_oers = OER.objects.filter(id__in=glossary_ids)
        result['glossaries'] = [glossary_filter_terms(glossary_to_tbx_dict(oer)) for oer in glossary_oers]
    result['domains'] = load_corpus_metadata(file_key).get('domains', [])
    data = json.dumps(result)
    endpoint = nlp_url + '/api/add_doc/'
    response = requests.post(endpoint, data=data)
    if not response.status_code==200:
        return propagate_remote_server_error(response)
    data = response.json()
    new_file_key = data['file_key']
    if new_file_key:
        if not new_file_key == file_key:
            rename_corpus_metadata(file_key, new_file_key)
            file_key = new_file_key
        result = {'file_key': file_key, 'index': result['index'], 'language': data['language'], 'n_tokens': data['n_tokens'], 'n_words': data['n_words']}
    else:
        result = {'file_key': file_key, 'error': 'languages cannot be mixed in corpus'}
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
    metadata = load_corpus_metadata(file_key)
    glossary_ids = metadata.get('glossaries', [])
    if glossary_ids:
        glossary_oers = OER.objects.filter(id__in=glossary_ids)
        glossaries = [glossary_filter_terms(glossary_to_tbx_dict(oer)) for oer in glossary_oers]
    domains = metadata.get('domains', [])
    data = json.dumps({'file_key': file_key, 'index': index, 'obj_type': obj_type, 'obj_id': obj_id, 'label': title, 'url': url, 'text': text, 'glossaries': glossaries, 'domains': domains})
    endpoint = nlp_url + '/api/add_doc/'
    response = requests.post(endpoint, data=data)
    if not response.status_code==200:
        return propagate_remote_server_error(response)
    data = response.json()
    new_file_key = data['file_key']
    if new_file_key:
        if not new_file_key == file_key:
            rename_corpus_metadata(file_key, new_file_key)
            file_key = new_file_key
        result = {'file_key': file_key, 'index': index, 'language': data['language'], 'n_tokens': data['n_tokens'], 'n_words': data['n_words']}
    else:
        result = {'file_key': file_key, 'error': 'languages cannot be mixed in corpus'}
    return JsonResponse(result)

@csrf_exempt
def ajax_resource_to_item(request):
    data = json.loads(request.body.decode('utf-8'))
    file_key = data['file_key']
    url = data['url']
    text = data['text']
    assert url or text
    if url:
        obj_type = 'web'
        title, text, response, err = get_web_resource_text(url)
        if err or not text:
            return propagate_remote_server_error(response)
        obj_id = hashlib.sha256(url.encode('utf-8')).hexdigest()
    elif text:
        obj_type = 'text'
        # title = 'untitled'
        obj_id = hashlib.sha256(text.encode('utf-8')).hexdigest()
        title_end = text.find('\n')
        title = text[:title_end]
        text = text[title_end+1:]
    result = {'file_key': file_key, 'index': None, 'obj_type': obj_type, 'obj_id': obj_id, 'label': title, 'url': url, 'text': text}
    return add_item_to_corpus(request, file_key, result)

@csrf_exempt
def ajax_file_to_item(request: HttpRequest, file_key: str) -> HttpResponse:
    """ called from contents_dashboard template to a file item to a corpus (docbin) """
    body = request.body
    domains = file_key and load_corpus_metadata(file_key).get('domains', []) or []
    content_type = request.content_type
    content_disposition = request.headers['Content-Disposition']
    title, text, err = get_file_text(body, content_type, title=content_disposition)
    obj_type = 'file'
    obj_id = hashlib.sha256(text.encode('utf-8')).hexdigest()
    result = {'file_key': file_key, 'index': None, 'obj_type': obj_type, 'obj_id': obj_id, 'label': title, 'url': None, 'text': text}
    return add_item_to_corpus(request, file_key, result)

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

"""
called from contents_dashboard template
to update an attribute in corpus metadata
"""
@csrf_exempt
def ajax_corpus_update(request):
    data = json.loads(request.body.decode('utf-8'))
    file_key = data['file_key']
    metadata = load_corpus_metadata(file_key)
    metadata[data['key']] = data['value']
    save_corpus_metadata(file_key, metadata)
    return JsonResponse(data)

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

"""
called from contents_dashboard template
to compare the texts of a list of resources
"""
@csrf_exempt
def ajax_compare_resources(request):
    data = json.loads(request.body.decode('utf-8'))
    resources = data['items']
    n = len(resources)
    if n == 0 or (n == 1 and resources[0]['obj_type'] != 'lp'):
        ajax_response = JsonResponse({"error": "Need at least 2 items"})
        ajax_response.status_code = 404
        return ajax_response
    elif n == 1:
        return lp_compare_nodes(request, resources[0]['obj_id'])
    else:
        user_key = '{id:05d}'.format(id=request.user.id)
        endpoint = nlp_url + '/api/delete_corpus/'
        data = json.dumps({'user_key': user_key})
        response = requests.post(endpoint, data=data)
        if not response.status_code==200:
            return propagate_remote_server_error(response)
        endpoint = nlp_url + '/api/add_doc/'
        last_language = None
        for resource in resources:
            title, description, text = get_obj_text(None, obj_type=resource['obj_type'], obj_id=resource['obj_id'], return_has_text=False, with_children=True)
            text = '{}, {}. {}'.format(title, title, text)
            doc_key = '{id:05d}'.format(id=resource['obj_id'])
            data = json.dumps({'user_key': user_key, 'doc_key': doc_key, 'text': text})
            response = requests.post(endpoint, data=data)
            if not response.status_code==200:
                return propagate_remote_server_error(response)
            data = response.json()
            language = data.get('language', '')
            if last_language and language!=last_language:
                ajax_response = JsonResponse({"error": "All items must have same language"})
                ajax_response.status_code = 404
                return ajax_response
            last_language = language
        endpoint = nlp_url + '/api/compare_docs/'
        data = json.dumps({'user_key': user_key, 'language': language})
        response = requests.post(endpoint, data=data)
        if response.status_code==200:
            result = response.json()
            return JsonResponse(result)
        else:
            return propagate_remote_server_error(response)

def corpus_dashboard_return(request, var_dict):
    if not var_dict:
        var_dict = { 'error': off_error }
    return JsonResponse(var_dict)

def corpus_dashboard(request, file_key=''):
    print('file_key', file_key)
    data = json.dumps({'file_key': file_key})
    endpoint = nlp_url + '/api/get_corpus'
    try:
        response = requests.post(endpoint, data=data)
        print('corpus_dasboard ok')
    except:
        response = None
        print('corpus_dasboard ko')
    if not response or response.status_code!=200:
        print('corpus_dasboard', response.status_code)
        return corpus_dashboard_return(request, {})
    corpus_dict = response.json()
    n_docs = len(corpus_dict)
    assert n_docs
    language = corpus_dict[0]['language']
    for doc_dict in corpus_dict:
        doc_dict['n_tokens'] = len(doc_dict['tokens'])
    lemma_pos_dict = LemmaPosDict(corpus_dict)
    lemma_pos_dict.make()
    cross_table = []
    for i in range(n_docs):
        row = []
        counts_i = lemma_pos_dict.get_counts(i)
        count_self = counts_i['n_self']
        count_unique = counts_i['n_diff_1']
        for j in range(n_docs):
            col = []
            if j == i:
                col.append(count_self)
                col.append(count_unique)
                col.append(int((count_unique * 100)/count_self))
            else:
                counts_i_j = lemma_pos_dict.get_counts(i, [j])
                diff_i_j = counts_i_j['n_diff_1']
                col.append(diff_i_j)
                col.append(int((diff_i_j * 100)/count_self))
            row.append(col)
        cross_table.append(row)
    var_dict = {'language': language, 'docs': corpus_dict, 'cross_table': cross_table}
    return corpus_dashboard_return(request, var_dict)

@csrf_exempt
def text_wordlists(request, file_key='', obj_type='', obj_id='', url=''):
    var_dict = {'file_key': file_key, 'obj_type': obj_type, 'obj_id': obj_id, 'url': url}
    var_dict['VUE'] = True
    if is_ajax(request):
        keys = ['verb_frequencies', 'noun_frequencies', 'adjective_frequencies', 'adverb_frequencies', 
                'propn_frequencies', 'cconj_frequencies', 'sconj_frequencies',
                'obj_type_label', 'language', 'title', 'label', 'url',]
        data = var_dict
        dashboard_dict = text_dashboard(request, file_key=file_key, obj_type=obj_type, obj_id=obj_id, wordlists=True)
        data.update([[key, dashboard_dict[key]] for key in keys])
        return JsonResponse(data)
    else:
        return render(request, 'text_wordlists.html', var_dict)

"""
called from contents_dashboard or text_analysis template
to find and sort document keywords and to list keyword in context
"""
@csrf_exempt
def context_dashboard(request, file_key='', obj_type='', obj_id='', url=''):
    var_dict = {'file_key': file_key, 'obj_type': obj_type, 'obj_id': obj_id, 'url': url}
    if is_ajax(request):
        # var_dict = text_dashboard(request, file_key=file_key, obj_type=obj_type, obj_id=obj_id, contexts=True)
        if not file_key:
            dashboard_dict = text_dashboard(request, obj_type=obj_type, obj_id=obj_id, contexts=True)
            var_dict['text'] = dashboard_dict['text']
            var_dict['title'] = dashboard_dict['title']
        endpoint = nlp_url + '/api/word_contexts/'
        data = json.dumps(var_dict)
        response = requests.post(endpoint, data=data)
        result = response.json()
        extended_attrs = result['extended_attrs']
        var_dict['obj_type_label'] = obj_type_label_dict[obj_type]
        var_dict['label'] = extended_attrs['label']
        url = extended_attrs['url']
        if url and len(url)> 2:
            var_dict['url'] = url
        var_dict['language'] = settings.LANGUAGE_MAPPING[result['language']]
        var_dict['keywords'] = result['keywords']
        var_dict['kwics'] = result['kwics']
        return JsonResponse(var_dict)
    else:
        return render(request, 'context_dashboard.html', var_dict)

def text_summarization(request, params):
    var_dict = text_dashboard(request, obj_type=params['obj_type'], obj_id=params['obj_id'], file_key=params['file_key'], url=params['url'], summarization=True)
    error = var_dict.get('error', None)
    if error:
        print('error:', error)
    else:
        del params['url']
        del params['title']
        del params['text']
        var_dict.update(params)
    return render(request, 'text_summarization.html', var_dict)

@csrf_exempt
def text_dependency(request, file_key='', obj_type='', obj_id='', url=''):
    var_dict = {'file_key': file_key, 'obj_type': obj_type, 'obj_id': obj_id, 'url': url}
    var_dict['VUE'] = True
    if is_ajax(request):
        keys = ['text', 'sentences', 'tokens', 'entities', 'entity_lists',
                'collData', 'docData',
                'obj_type_label', 'language', 'title', 'label', 'url']
        data = var_dict
        dashboard_dict = text_dashboard(request, file_key=file_key, obj_type=obj_type, obj_id=obj_id, dependency=True)
        data.update([[key, dashboard_dict[key]] for key in keys])
        return JsonResponse(data)
    else:
        return render(request, 'text_dependency.html', var_dict)

@csrf_exempt
def text_nounchunks(request, file_key='', obj_type='', obj_id='', url='', glossary_id=''):
    var_dict = {'file_key': file_key, 'obj_type': obj_type, 'obj_id': obj_id, 'url': url, 'glossary_id': glossary_id}
    
    var_dict['VUE'] = True
    if is_ajax(request):
        data = var_dict
        tbx_dict = {}
        if glossary_id:
            oer_glossary = OER.objects.get(id=glossary_id)
            tbx_dict = glossary_to_tbx_dict(oer_glossary)
        keys = ['paragraphs', 'tokens', 'noun_chunks', 'bn_terms', 'gl_terms',
                'obj_type_label', 'language', 'title', 'label', 'url',]
        dashboard_dict = text_dashboard(request, file_key=file_key, obj_type=obj_type, obj_id=obj_id, tbx_dict=tbx_dict, nounchunks=True)
        data.update([[key, dashboard_dict[key]] for key in keys])
        data['type_buttons'] = span_type_buttons
        data['user_language_code'] = request.LANGUAGE_CODE
        data['user_language'] = dict(settings.LANGUAGES).get(request.LANGUAGE_CODE, _('unknown'))
        if file_key:
            glossary_ids = load_corpus_metadata(file_key).get('glossaries', [])
            if glossary_ids:
                glossary_oers = OER.objects.filter(id__in=glossary_ids)
                data['glossary'] = glossary_to_tbx_dict(glossary_oers[0])
        elif glossary_id:
            data['glossary'] = tbx_dict
        span_types = define_span_types()
        if not data.get('noun_chunks', []):
            span_types.remove('nounchunk')
        if not data['gl_terms']:
            span_types.remove('glossary')
        if not data['bn_terms']:
            span_types.remove('babelnet')
        data['span_types'] = span_types
        return JsonResponse(data)
    else:
        return render(request, 'text_nounchunks.html', var_dict)

def normalize_entity_graph_score(key_score, mean_sentence_length):
    key, score = key_score
    normalized_score = score / mean_sentence_length
    normalized_score = math.pow(normalized_score, 1/3)
    return key, normalized_score 

@csrf_exempt
def text_annotation(request, file_key='', obj_type='', obj_id='', url=''):
    var_dict = {'file_key': file_key, 'obj_type': obj_type, 'obj_id': obj_id, 'url': url}
    var_dict['VUE'] = True
    if is_ajax(request):
        keys = ['paragraphs', 'language', 'obj_type_label', 'title', 'label',]
        data = var_dict
        dashboard_dict = text_dashboard(request, file_key=file_key, obj_type=obj_type, obj_id=obj_id, text_annotation=True)
        data.update([[key, dashboard_dict[key]] for key in keys])
        data['tokens'] = dashboard_dict['doc']['tokens']
        data['color_dict'] = color_dict
        data['pos_list'] = pos_list
        data['pos_map'] = pos_map
        return JsonResponse(data)
    else:
        return render(request, 'text_annotation.html', var_dict)

@csrf_exempt
def text_cohesion(request, file_key='', obj_type='', obj_id='', url=''):
    var_dict = {'file_key': file_key, 'obj_type': obj_type, 'obj_id': obj_id, 'url': url}
    var_dict['VUE'] = True
    if is_ajax(request):
        keys = ['paragraphs', 'repeated_lemmas',
                'cohesion_by_repetitions', 'cohesion_by_similarity', 
                'obj_type_label', 'language', 'title', 'label', 'url']
        dashboard_dict = text_dashboard(request, file_key=file_key, obj_type=obj_type, obj_id=obj_id, text_cohesion=True)

        # normalize cohesion_by_entity_graph scores between 0 and 1
        mean_sentence_length = dashboard_dict['mean_sentence_length']     
        cohesion_by_entity_graph = []
        for key_score in dashboard_dict['cohesion_by_entity_graph']:
            cohesion_by_entity_graph.append(normalize_entity_graph_score(key_score, mean_sentence_length ))

        data = var_dict
        data['cohesion_by_entity_graph'] = cohesion_by_entity_graph
        data.update([[key, dashboard_dict[key]] for key in keys])
        data['tokens'] = dashboard_dict['doc']['tokens']
        data['color_list'] = color_list
        data['color_dict'] = color_dict
        repeated_lemmas = dashboard_dict['repeated_lemmas'][:20]
        data['repeated_lemmas'] = repeated_lemmas
        data['lemma_color_map'] = lemmas_to_colors(repeated_lemmas, color_list, color_dict)
        return JsonResponse(data)
    else:
        return render(request, 'text_cohesion.html', var_dict)

def text_readability(request, params):
    var_dict = text_dashboard(request, obj_type=params['obj_type'], obj_id=params['obj_id'], file_key=params['file_key'], url=params['url'], readability=True)
    error = var_dict.get('error', None)
    if error:
        print('error:', error)
    else:
        del params['title']
        del params['url']
        var_dict.update(params)
    language_code = var_dict['language_code']
    n_sentences = var_dict['n_sentences']
    n_tokens = var_dict['n_tokens']
    mean_sentence_length = var_dict['mean_sentence_length']
    n_words = var_dict['n_words'] or 1
    n_word_characters = var_dict['n_word_characters']
    mean_chars_per_word = n_word_characters / n_words
    var_dict['mean_chars_per_word'] = mean_chars_per_word
    n_word_syllables = var_dict['n_word_syllables']
    mean_syllables_per_word = n_word_syllables / n_words
    var_dict['mean_syllables_per_word'] = mean_syllables_per_word
    voc_density = var_dict['voc_density']
    lexical_rarity = compute_lexical_rarity(var_dict['levels_counts'])
    var_dict['lexical_rarity'] = lexical_rarity
    mean_dependency_depth = var_dict['mean_dependency_depth']
    mean_dependency_distance = var_dict['mean_dependency_distance']

    pos_frequencies = var_dict['pos_frequencies']
    n_adjectives = pos_frequencies.get('ADJ', 0)
    n_adverbs = pos_frequencies.get('ADV', 0)
    n_pronouns = pos_frequencies.get('PRON', 0)
    var_dict['adverbs_adjectives_ratio'] = n_adjectives and n_adverbs / n_adjectives or 0
    var_dict['adjectives_pronouns_ratio'] = n_pronouns and n_adjectives / n_pronouns or 0

    var_dict['readability_indexes_keys'] = readability_indexes_keys
    var_dict['readability_indexes'] = {}
    index = readability_indexes['flesch_easy']
    if language_code in index['languages']:
        index['value'] = 206.835 - 1.015 * mean_sentence_length - 84.6 * mean_syllables_per_word
        index['range'] = readability_level('flesch_easy', index['value'])
        var_dict['readability_indexes']['flesch_easy'] = index
    index = readability_indexes['kincaid_flesh']
    if language_code in index['languages']:
        index['value'] = 0.39 * mean_sentence_length + 11.8 * mean_syllables_per_word - 15.59
        index['range'] = readability_level('kincaid_flesh', index['value'])
        var_dict['readability_indexes']['kincaid_flesh'] = index
    index = readability_indexes['brangan_rasprave']
    if language_code in index['languages']:
        index['value'] = 206.835 - 1.015 * mean_sentence_length - 84.6 * mean_syllables_per_word + 50
        index['range'] = readability_level('flesch_easy', index['value'])
        var_dict['readability_indexes']['flesch_easy'] = index
    index = readability_indexes['franchina_vacca_1972']
    if language_code in index['languages']:
        index['value'] = 206 - mean_sentence_length - 65 * mean_syllables_per_word
        index['range'] = readability_level('flesch_easy', index['value'])
        var_dict['readability_indexes']['franchina_vacca_1972'] = index
    index = readability_indexes['gulp_ease']
    if language_code in index['languages']:
        index['value'] = 89 - 10 * mean_chars_per_word + 100 * n_sentences / n_words
        index['range'] = readability_level('flesch_easy', index['value'])
        var_dict['readability_indexes']['gulp_ease'] = index
    index = readability_indexes['fernandez_huerta']
    if language_code in index['languages']:
        index['value'] = 206.84 - 1.02 * mean_sentence_length - 60 * mean_syllables_per_word
        index['range'] = readability_level('flesch_easy', index['value'])
        var_dict['readability_indexes']['fernandez_huerta'] = index
    index = readability_indexes['gagatsis_1985']
    if language_code in index['languages']:
        index['value'] = 206.835 - 1.015 * mean_sentence_length - 59 * mean_syllables_per_word
        index['range'] = readability_level('flesch_easy', index['value'])
        var_dict['readability_indexes']['gagatsis_1985'] = index
    index = readability_indexes['björnsson_1968']
    if language_code in index['languages']:
        lix = mean_sentence_length + var_dict['n_long_tokens'] * 100 / n_tokens # mean_sentence_length = n_tokens/n_sentences
        index['value'] = (100 - lix) * 100 / 75
        index['range'] = readability_level('björnsson_1968', index['value'])
        var_dict['readability_indexes']['björnsson_1968'] = index
    index = readability_indexes['cs_readability_01']
    index['value'] = cs_readability_01(language_code, mean_sentence_length, mean_syllables_per_word, mean_dependency_depth, mean_dependency_distance, voc_density, lexical_rarity)
    index['range'] = readability_level('flesch_easy', index['value'])
    var_dict['readability_indexes']['cs_readability_01'] = index
    return render(request, 'text_readability.html', var_dict)

def ta_input(request):
    var_dict = {}
    if request.POST:
        form = TextAnalysisInputForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            function = data['function']
            request.session['text'] = data['text']
            glossary = data.get('glossary', None)
            if function == 'dashboard': # Text Analysis Dashboard
                var_dict = {'obj_type': 'text', 'obj_id': 0, 'VUE': True}
                return render(request, 'text_dashboard.html', var_dict)
            else:
                glossary_id = glossary and glossary.id or None
                return ta(request, function, obj_type='text', obj_id=0, glossary_id=glossary_id)
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
    return render(request, 'ta_input.html', var_dict)

def ta(request, function, obj_type='', obj_id='', file_key='', url='', text='', title='', glossary_id=''):
    var_dict = { 'obj_type': obj_type, 'obj_id': obj_id, 'file_key': file_key, 'url': url, 'text': text, 'title': '' }
    var_dict['VUE'] = True
    if file_key:
        if obj_type == 'corpus':
            var_dict['obj_type'] = ''
    else:
        var_dict['obj_type_label'] = obj_type_label_dict[obj_type]
        if obj_type == 'text':
                var_dict['obj_id'] = 0
    if function == 'corpus':
        return render(request, 'corpus_dashboard.html', var_dict)
    elif function == 'dashboard':
        return render(request, 'text_dashboard.html', var_dict)
    elif function == 'dependency':
        return render(request, 'text_dependency.html', var_dict)
    elif function == 'context':
        return render(request, 'context_dashboard.html', var_dict)
    elif function == 'annotations':
        return render(request, 'text_annotation.html', var_dict)
    elif function == 'summarization':
        return text_summarization(request, params=var_dict)
    elif function == 'readability':
        return text_readability(request, params=var_dict)
    elif function == 'cohesion':
        return render(request, 'text_cohesion.html', var_dict)
    elif function == 'nounchunks':
        if glossary_id:
            var_dict['glossary_id'] = glossary_id
        return render(request, 'text_nounchunks.html', var_dict)
    elif function == 'wordlists':
        return render(request, 'text_wordlists.html', var_dict)

@csrf_exempt
def tbx_view(request, file_key='', obj_type='', obj_id='', url=''):
    var_dict = {'file_key': file_key, 'obj_type': obj_type, 'obj_id': obj_id, 'url': url}
    if obj_type:
        var_dict['obj_type_label'] = obj_type_label_dict[obj_type]
    var_dict['VUE'] = True
    if is_ajax(request):
        data = var_dict
        document = get_object_or_404(Document, id=obj_id)
        data['title'] = document.label
        f = document.open()
        xml_str = f.read()
        tbx_dict = tbx_xml_2_dict(xml_str, split_subjects=True)
        tbx = tbx_dict['tbx']
        concepts = tbx['text']['body']['conceptEntry']
        data['concepts'] = concepts
        data['languages'] = tbx_languages(concepts)
        data['subjects'] = tbx_subjects(concepts)
        index = tbx['text']['index']
        columns = index['conceptColumns'] + index['langColumns'] + index['termColumns']
        data['columns'] = columns
        return JsonResponse(data)
    else:
        return render(request, 'tbx_view.html', var_dict)

def glossary_to_tbx_dict(oer_glossary):
    """convert an OER with a .tbx attachment to a tbx_dict format
    """
    tbx_dict = {}
    document = None
    for d in oer_glossary.get_sorted_documents():
        if d.label.endswith('.tbx'):
            document = d
            break
    if document:
        f = document.open()
        xml_str = f.read()
        tbx_dict = tbx_xml_2_dict(xml_str)
    return tbx_dict

def glossary_filter_terms(tbx_dict, languages=[]):
    """from a glossary in tbx_dict format extract a list of concepts 
    with the associated terms, possibly filtered for the specified language(s)
    """
    concepts = tbx_dict['tbx']['text']['body']['conceptEntry']
    return tbx_filter_by_language(concepts, languages=languages)

def get_all_glossaries(request):
    view_states = (settings.SITE_ID==1 or not is_site_member(request.user)) and [PUBLISHED] or [RESTRICTED, PUBLISHED]
    qs = OER.objects.filter(state__in=view_states, documents__label__icontains='.tbx')
    qs = qs.filter_by_site(OER)
    return qs

def glossary_autocomplete(request):
    MIN_CHARS = 2
    q = request.GET.get('q', None)
    create_option = []
    results = []
    if request.user.is_authenticated:
        if q and len(q) >= MIN_CHARS:
            """
            view_states = (settings.SITE_ID==1 or not is_site_member(request.user)) and [PUBLISHED] or [RESTRICTED, PUBLISHED]
            qs = OER.objects.filter(state__in=view_states, title__icontains=q, documents__label__icontains='.tbx').order_by('title')
            qs = qs.filter_by_site(OER)
            """
            qs = get_all_glossaries(request)
            qs = qs.filter(title__icontains=q).order_by('title')
            results = [{'id': oer.id, 'text': oer.title[:80]} for oer in qs] + create_option
    body = json.dumps({ 'results': results, 'more': False, })
    return HttpResponse(body, content_type='application/json')
