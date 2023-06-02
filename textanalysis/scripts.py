
def txt_esteban_to_json(filepath: str, es_key='Glosario en español', en_key='Glossary in English') -> str:
    with open(filepath, 'r', encoding="utf8") as f:
        language = None
        line = f.readline()
        while line:
            if len(line) <= 2 or line.startswith('#'):
                line = f.readline()
                continue
            if line.startswith(es_key):
                language = 'es'
                heading = line
                print(heading)
                line = f.readline()
                continue
            elif line.startswith(en_key):
                language = 'en'
                heading = line
                print(heading)
                line = f.readline()
                continue
            tokens = line.split()
            n_tokens = len(tokens)
            if n_tokens >= 2 and tokens[0].endswith('.'):
                first = tokens[0].replace('.', '').strip()
                number = int(first)
                term = ' '.join(tokens[1:])
                if term[-1] in ['.', ':']:
                    term = term[:-1]
                definition = f.readline()
                print(language, number, term, definition)
            line = f.readline()

def txt_pena_to_json(filepath: str) -> str:
    with open(filepath, 'r', encoding="utf8") as f:
        language = None
        line = f.readline()
        while line:
            if len(line) <= 2 or line.startswith('#'):
                line = f.readline()
                continue
            tokens = line.split()
            n_tokens = len(tokens)
            if n_tokens >= 2 and tokens[0].endswith('.'):
                first = tokens[0].replace('.', '').strip()
                number = int(first)

                language = 'es'
                line = ' '.join(tokens[1:])
                splitted = line.split(':')
                term = splitted[0]
                definition = ':'.join(splitted[1:])
                print(language, number, term, definition)

                line = f.readline().strip()
                tokens = line.split()
                assert tokens[0] == '—'
                language = 'en'
                line = ' '.join(tokens[1:])
                splitted = line.split(':')
                term = splitted[0]
                definition = ':'.join(splitted[1:])
                print(language, number, term, definition)
            line = f.readline()
