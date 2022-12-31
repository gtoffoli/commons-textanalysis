vowels = 'aeiouy'
hard_cons = 'bcdfgjpqstvwxz'
liquid_cons = 'hlmnr'
cons = hard_cons + liquid_cons

def count_word_syllables(word):
    n_chars = len(word)
    word = word + '  '
    n_syllables = 0
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
    return n_syllables