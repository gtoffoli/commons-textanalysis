import os

pos_upos_map = {
    'A':    'ADJECTIVE',
    'CC':   'CCONJ',
    'SC':   'SCONJ',
    'D':    'ADVERB',
    'I':    'INTJ',
    'L':    'NUM',
    'LW':   'NUM',
    'NC':   'NOUN',
    'NP':   'PROPN', 
    'NW':   'NOUN',
    'P':    'PRON',
    'T':    'ADP',
    'V':    'VERB',
}

CEFR_LEVELS = { # level codes are case-insensitive
    0: 'a1',
    1: 'a2',
    2: 'b1',
    3: 'b2',
    4: 'c1',
    5: 'c2',
}

FREQUENCY_INTERVALS = { # level codes are case-insensitive
    'NOUN': [400, 500, 600, 700, 800, 900,],
    'VERB': [200, 250, 300, 300, 300, 300,],
    'ADJECTIVE': [200, 250, 300, 300, 300, 300],
    'ADVERB': [50, 60, 70, 80, 80, 80],
}

def frequency_to_level(index, intervals):
    level = 0
    max_index = 0
    for interval in intervals:
        max_index += interval
        if index > max_index:
            level += 1
            if level == len(CEFR_LEVELS):
                return None
    return CEFR_LEVELS[level]  

token_level_dict = {}

def get_vocabulary():
    return token_level_dict

def load_vocabulary(file_name='lemma-12k-2017.txt'):
    """ builds in memory
    """
    global token_level_dict
    lexicon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name)
    indexes = {
        'NOUN': 0,
        'VERB': 0,
        'ADJECTIVE': 0,
        'ADVERB': 0,
    }
    with open(lexicon_path, encoding='utf8') as infile:
        line = infile.readline()
        while line:
            pos, lemma, frequency = line.split('\t')
            upos = pos_upos_map.get(pos, pos)
            if not upos in ['NOUN', 'VERB', 'ADJECTIVE', 'ADVERB',]:
                line = infile.readline()
                continue
            level = frequency_to_level(indexes[upos], FREQUENCY_INTERVALS[upos])
            indexes[upos] += 1
            if not level:
                line = infile.readline()
                continue
            token_level_dict[lemma.lower()+'_'+upos.lower()] = level
            line = infile.readline()

load_vocabulary(file_name='lemma-12k-2017.txt')
