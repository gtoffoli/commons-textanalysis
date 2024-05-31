import os
import re
import pyexcel

file_name = 'KELLY_AR.xlsx'
source = 'https://inventory.clarin.gr/lcr/741'
attribution = """KELLY word-list Arabic by University of Leeds, used under Creative Commons Attribution Non Commercial 4.0 International (https://creativecommons.org/licenses/by-nc/4.0/legalcode, https://creativecommons.org/licenses/by-nc/4.0/). Source: https://ssharoff.github.io/kelly/ar_m3.xls from https://ssharoff.github.io/kelly/ """

# from camel_tools.utils modules: TATWEEL is not a regular diacritic !!!
AR_DIAC_CHARSET = frozenset(u'\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652'
                            u'\u0670\u0640')

_DIAC_RE_AR = re.compile(u'[' +
                         re.escape(u''.join(AR_DIAC_CHARSET)) +
                         u']')
def dediac_ar(s):
    """Dediacritize Unicode Arabic string.

    Args:
        s (:obj:`str`): String to dediacritize.

    Returns:
        :obj:`str`: Dediacritized string.
    """

    return _DIAC_RE_AR.sub(u'', s)


# Part of speech
pos_map = {
   'اسم': ['noun'],
   'اسم من الأسماء الخمسة': ['noun'], # 'one of the five names'
   'مصطلح عامى': ['noun'], # colloquial term
   'اسم علم': ['noun'], # proper noun
   'اسم مكان': ['noun'] , # noun of place
   'مصطلح دينى': ['noun'], # religious term
   'مصطلح سياسى': ['noun'], # 'political term'
   'اسم منسوب': ['noun'], # 'assigned name' ?
   'اسم (مضاف ومضاف إليه)': ['noun'], # 'genitive and genitive' ?
   'اسم يدل على المساحة': ['noun'], # 'a name that indicates space' e.g. Acres
   'أداة جزم':  ['noun'], # shoe related ?
   'ضمير': ['pronoun'],
   'للاشارة': ['pronoun'], # 'to sign' (suffix ?)
   'صفة': ['adjective'],
   'اسم تفضيل': ['noun', 'adjective'], # 'preference noun'
   'اسم إشارة': ['pronoun, adjective'], # 'demonstrative noun'
   'اسم اشارة': ['pronoun, adjective'], # 'demonstrative noun'
   'اسم للمثنى': ['pronoun, adjective'], # 'a name for the two'
   'عدد': ['noun', 'adjective'], # number
   'مصطلح عددى': ['noun', 'adjective'], # 'numerical term'
   'اصفة': ['adjective'], # 'descriptive'
   'فعل': ['verb'],
   'فعل أمر': ['verb'], # 'imperative mood'
   'اقعل': ['verb'], # auxiliar verb ?
   'فعل منفى': ['verb'], # negative verb
   'كشف': ['verb'], # 'statement'
   'ظرف': ['adverb'],
   'ظرف زمان': ['adverb'], # time adverb
   'ظرف مكان': ['adverb'], # place adverb
   'شبه جملة': ['adverb'], # 'phrase-like' (preposition+genitive)
   'جار ومجرور': ['adverb'], # 'preposition and genitive'
   'حرف+لا الناهية': ['adverb'], # 'particle + negation'
   'حرف': ['adverb', 'pronoun', 'preposition', 'conjunction'], # 'particle'
   'حرف جر': ['preposition'], # 'particle preposition'
   'حرف عطف': ['conjunction'], # 'particle conjunction'
   'حرف توكيد ونصب': ['conjunction'], # particle subordinating conjunction ?
   'كى: أداة نصب للمضارع': ['conjunction'], # present tense accusative construct ?
   'للمقارنة': ['conjunction'], # comparison
   'من أخوات إن': ['conjunction', 'preposition'], # 'Inna and its sisters'
   'أداة نفى': ['adverb', 'pronoun', 'exclamation'], # negation
   'حرف توكيد': ['adverb', 'exclamation'], # 'particle affirmative, negative, enphasis'
   'كلمة عامية': ['adverb', 'exclamation'], # 'slang word'
   'للنفى': ['adverb', 'exclamation'], # exclusion ?
   'للتوكيد': ['noun', 'verb', 'exclamation'], # 'enphasis, confirmation'
   'أداة توكيد': ['noun', 'verb', 'exclamation'], # enphasis construct
   'حرف تأكيد ونصب': ['adverb', 'exclamation'], # 'particle affirmative'
   'بمعنى نعم': ['adverb', 'exclamation'], # affirmative
   'بناء: اسم - على: حرف': ['preposition', 'conjunction'], # prepositional locution
   'حال': ['adverb', 'preposition', 'conjunction'], # 'condition'
   'حرف نصب': ['adverb', 'preposition', 'conjunction'], # 'particle accusative'
   'أداة شرط': ['adverb', 'conjunction'], # conditional construct
   'أداة نصب': ['preposition', 'conjunction'], # 'setup ..'
   'ردا: اسم - على: حرف': ['adverb', 'preposition'], # 'in reply to'
   'مفعول مطلق': ['adverb', 'exclamation'], # 'absolute object'
   'أداة استثناء': ['conjunction', 'preposition'], # 'exception'
   'أداة استفهام': ['adjective', 'pronoun', 'adverb', 'conjunction'], # 'question mark'
   'اداة استفهام': ['adjective', 'pronoun', 'adverb', 'conjunction'], # 'question mark'
   'للاستفهام': ['adjective', 'pronoun', 'adverb', 'conjunction'], # 'question mark'
   'أداة تعججب': ['exclamation'],
   'للدعاء': ['noun', 'exclamation', 'verb'], # 'prayer, invocation'
   'مصطلح للدعاء': ['noun', 'exclamation', 'verb'], # 'a term for supplication/prayer'
   'جملة للدعاء': ['noun', 'exclamation', 'verb'], # 'a term for supplication/prayer'
   'جملة اعتراضية للدعاء':  ['noun', 'exclamation', 'verb'], # 'exclamation for supplication'
   'للتحذير': ['noun', 'exclamation', 'verb'], # 'warning'
   'جملة للتحية': ['noun', 'exclamation', 'verb'], # 'greetings'
   'حرف نداء': ['exclamation'], # 'call'
   'اختصار': ['noun'], # abbreviation
   'مصطلح دينى للدعاء': [], # prayer religious term
   'حرف+ضمير': [], # preposition + pronoun
}

voc_cols_dict = {
    'CEFR level': 5,
    'Lemma': 4,
    'POS': 2,
}
# the vocabulary annotated with CEFR level to be created by interpreting the KELLY_AR file
voc_ar = [
]

def split_postag(postag):
    postags = set()
    els = [x.strip() for x in postag.split('/')]
    for el in els:
        postags.update(pos_map[el.lower()])
    return list(postags)

def make_entries(voc_cols_dict, row):
    entries = []
    level = row[voc_cols_dict['CEFR level']]
    lemma = dediac_ar(row[voc_cols_dict['Lemma']])
    postag = row[voc_cols_dict['POS']]
    postags = split_postag(postag)
    for postag in postags:
        entries.append([lemma, postag, level.lower()])
    return entries

def load_vocabulary (file_name=''):
    global voc_ar
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name)
    f = open(file_path, "br")
    extension = file_name.split(".")[-1]
    content = f.read()
    f.close()
    book = pyexcel.get_book(file_type=extension, file_content=content)
    book_dict = book.to_dict()
    voc_table = book_dict["Arabic"]
    voc_cols = voc_table[0]
    voc_rows = voc_table[1:]
    for row in voc_rows:
        voc_ar.extend(make_entries(voc_cols_dict, row))

load_vocabulary(file_name)

for i, entry in enumerate(voc_ar):
    print(i, entry)
