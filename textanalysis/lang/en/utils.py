vowels = 'aeiouy'

def count_word_syllables(word):
    n_chars = len(word)
    word = word + '  '
    n_syllables = 0
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
    return n_syllables