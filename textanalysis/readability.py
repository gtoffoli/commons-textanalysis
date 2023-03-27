readability_indexes = {
  'flesch_easy': { 'languages': ['en'], 'title': "Flesch Reading Ease score for English (0-100)", 'ref': 'https://en.wikipedia.org/wiki/Flesch%E2%80%93Kincaid_readability_tests' },
  'brangan_rasprave': { 'languages': ['hr'], 'title': "Brangan-Rasprave readability index for Croatian (0-100)", 'ref': 'https://www.researchgate.net/publication/289809226_Quantitative_Assessment_of_Text_Difficulty_in_Croatian_Language' },
  'franchina_vacca_1972': { 'languages': ['it'], 'title': "Franchina-Vacca readability index for Italian (0-100)", 'ref': 'https://it.wikipedia.org/wiki/Formula_di_Flesch' },
  'gulp_ease': { 'languages': ['it'], 'title': "GULP readability index for Italian (0-100)", 'ref': 'https://it.wikipedia.org/wiki/Indice_Gulpease' },
  'kincaid_flesh': { 'languages': ['en'], 'title': "Flesch–Kincaid grade level for English (Very easy-Extra difficult)", 'ref': 'https://en.wikipedia.org/wiki/Flesch%E2%80%93Kincaid_readability_tests' },
  'fernandez_huerta': { 'languages': ['es'], 'title': "Fernandez Huerta readability index for Spanish (0-100)", 'ref': 'https://legible.es/blog/lecturabilidad-fernandez-huerta/' },
  'gagatsis_1985': { 'languages': ['el'], 'title': "Gagatsis readability index for Greek (0-100)", 'ref': 'http://www.sfs.uni-tuebingen.de/~dm/papers/Georgatou-16.pdf' },
  'björnsson_1968': { 'languages': ['lt', 'it', 'en'], 'title': "LIX readability index by Björnsson, for Sweedish and generic (0-100)", 'ref': 'https://en.wikipedia.org/wiki/Lix_(readability_test)' },
  'cs_readability_01': { 'languages': [], 'title': "CommonSpaces readability index (0-100)", 'ref': 'https://docs.google.com/document/d/1Gx95rGWuxAomZwMttyhvT33AnTJVSIeSJf1xeOIE2Zc/' },
}
# gagatsis_1985. see: http://www.sfs.uni-tuebingen.de/~dm/papers/Georgatou-16.pdf
readability_indexes_keys = [
   'flesch_easy', # 'kincaid_flesh',
   'brangan_rasprave',
   'franchina_vacca_1972', # 'gulp_ease',
   'fernandez_huerta',
   'gagatsis_1985',
   'björnsson_1968',
   'cs_readability_01',
]

readability_scales = {
    'flesch_easy': [[90, 100, 'very easy'], [80, 90, 'easy'], [70, 80, 'fairly easy'], [60, 70, 'intermediate'], [50, 60, 'fairly difficult'], [30, 50, 'difficult'], [0, 30, 'very difficult'],],
    'kincaid_flesh': [[90, 100, '5th grade'], [80, 90, '6th grade'], [70, 80, '7th grade'], [60, 70, '8-9th grade'], [50, 60, '10-12 grade'], [30, 50, 'college'], [10, 30, 'college graduate'], [0, 10, 'professional'],],
    'cs_readability': [[80, 100, 'very easy'], [60, 80, 'easy'], [40, 60, 'intermediate'], [20, 40, 'difficult'], [0, 20, 'very difficult'],],
}
readability_scales['gagatsis_1985'] = readability_scales['flesch_easy'] 
readability_scales['fernandez_huerta'] = readability_scales['flesch_easy'] 
readability_scales['björnsson_1968'] = readability_scales['flesch_easy'] 
readability_scales['cs_readability'] = readability_scales['flesch_easy'] 

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

cs_01_weights = [
    # 30, # sentence_length: 
    # 5, # syllables_per_word
    35, # basic index = combination of sentence_length, syllables_per_word or % of long words
    10, # dependency_depth
    15, # dependency_distance
    10, # voc_density
    30, # lexical_rarity
]

def cs_readability_01(language_code, mean_sentence_length, mean_syllables_per_word, mean_dependency_depth, mean_dependency_distance, voc_density, lexical_rarity):
    """
    sentence_length = (20 - mean_sentence_length) / 5
    syllables_per_word = (2 - mean_syllables_per_word) / 0.5
    """
    for key in readability_indexes_keys:
        if key != 'cs_readability_01': # this index value hasn't been computed yet!
            index = readability_indexes[key]
            if language_code in index['languages']:
                basic = index['value'] # this index value should have been computed already!
                break
    dependency_depth = (1.5 - mean_dependency_depth) / 0.8
    dependency_distance = (4.0 - mean_dependency_distance) / 1.5
    lexical_sparseness = (0.70 - voc_density) / 0.15
    lexical_commonness = (0.60 - lexical_rarity) / 0.20
    components = (
        # sentence_length ,
        # syllables_per_word ,
        basic,
        dependency_depth ,
        dependency_distance ,
        lexical_sparseness ,
        lexical_commonness
    )
    index_value = 0
    for i, c in enumerate(components):
        if i == 0:
            index_value += min(100, c) * cs_01_weights[i] / 100 # vas already in scale 0-100
        else:
            index_value += min(1, c) * cs_01_weights[i] # was in scale 0-1
    return index_value