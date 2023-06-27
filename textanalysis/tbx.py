import os
import json
import csv
import xmltodict
from xml.etree.ElementTree import Element, tostring

from .utils import read_input_file, write_output_file, join_blankspaces

# define the sort order, useful for the rendeing
ALL_CONCEPT_COLUMNS = ['id', 'subjects',]
ALL_LANG_COLUMNS = ['lang', 'definition', 'def_source',]
ALL_TERM_COLUMNS = ['term', 'type', 'POS', 'status', 'reliability', 'term_source', 'context',]

TBX_DICT_2_XML_MAP = {
    'conceptEntry': 'conceptEntry',
    'id': '-id',
    'subjects': 'descrip-subjectField',
    'lang': '-xml:lang',
    'definition': 'descripGrp descrip-definition',
    'def_source': 'descripGrp admin-source',
    'term': 'term',
    'type': 'termNote-termType',
    'POS': 'termNote-partOfSpeech',
    'status': 'termNote-administrativeStatus',
    'reliability': 'termNote-reliabilityCode',
    'term_source': 'descripGrp admin-source',
    'context': 'descripGrp descrip-context',
}

def set_excel_header(response, filename):
    mimetype = 'application/vnd.ms-excel'
    response['Content-Type'] = '%s; charset=utf-8' % mimetype
    response['Content-Disposition'] = 'attachment; filename=%s.csv' % filename
    return response

def tbx_languages(concepts):
    """ tbx_languages
    return unique sorted languages from a tbx_dict - used only for the UI
    """
    languages = set()
    for concept in concepts:
        langSec = concept['langSec']
        try:
            lang = langSec.get('lang', None)
            languages.add(lang)
        except:
            for item in langSec:
                languages.add(item['lang'])
    return sorted(list(languages))

def tbx_subjects(concepts):
    """ tbx_subjects
    return unique sorted subjects from a tbx_dict - used only for the UI
    """
    all_subjects = set()
    for concept in concepts:
        subjects = concept.get('subjects', [])
        for subject in subjects:
            all_subjects.add(subject.strip())
    return sorted(list(all_subjects), key=lambda x: x.lower())

def tbx_filter_by_language(concepts, languages=[], merge_sort=False):
    """ tbx_filter_by_language
    if merge_sort is True, return sorted terms from a tbx_dict, possibly filtered by languages,
    else, return a list of concepts with associated terms,  possibly filtered by languages
    """
    glossary = []
    terms = []
    for concept in concepts:
        lang_items = concept['langSec'] 
        lang_terms = {}
        for lang_item in lang_items:
            if not languages:
                lang = lang_item['lang']
            elif not lang_item['lang'] in languages:
                continue
            term_items = lang_item['termSec']
            for term_item in term_items:
                terms.append(term_item['term'])
            if not languages and not merge_sort:
                lang_terms[lang] = terms
                terms = []
        if not merge_sort:
            if languages:
                glossary.append([concept['id'], terms])
            else:
                glossary.append([concept['id'], lang_terms])
            terms = []
    if merge_sort:
        return sorted(terms)
    else:
        return glossary
     
def parse_xml(xml_str: str) -> str:
    """ parse_xml
    Takes an xml string and returns the json equivalent.
    """
    return json.dumps(xmltodict.parse(xml_str))

def tbx_xml_2_dict(tbx_str: str, split_subjects=False) -> dict:
    """ tbx_xml_2_dict
    Takes an xml string and returns the equivalent Python dict slightly simpliflied.
    Adds an 'index' section intended to make easier the terminology/glossary rendering in tabular form.
    """
    json_str = parse_xml(tbx_str)

    # specify how to flatten the tbx structure
    json_str = json_str.replace('@xml:lang', 'lang')
    json_str = json_str.replace('"@type": "reliabilityCode", "#text":', '"reliabilityCode":')
    json_str = json_str.replace('"@type": "termType", "#text":', '"termType":')
    json_str = json_str.replace('"@type": "subjectField", "#text":', '"subjectField":')
    json_str = json_str.replace('"@type": "administrativeStatus", "#text":', '"administrativeStatus":')
    json_str = json_str.replace('"@type": "context", "#text":', '"context":')
    json_str = json_str.replace('"@type": "partOfSpeech", "#text":', '"partOfSpeech":')
    json_str = json_str.replace('"@type": "definition", "#text":', '"definition":')
    json_str = json_str.replace('"@type": "source", "#text":', '"source":')

    py_dict = json.loads(json_str)

    langs = set()
    columns = set(['id', 'lang', 'term',])
    concepts = py_dict['tbx']['text']['body']['conceptEntry']
    concept_dicts = []
    for concept in concepts:
        concept_dict = {'id': concept['@id']}
        lang = type(concept['langSec']) is dict and concept['langSec'].get('lang', None)
        if lang:
            concept['langSec'] = [{'lang': lang, 'termSec': concept['langSec']['termSec']}]
        subjectField = concept.get('descrip', '')
        subjects = subjectField and subjectField.get('subjectField', '') or ''
        if subjects:
            columns.add('subjects')
            if split_subjects:
                subjects = subjects.split(';') or []
        concept_dict['subjects'] = subjects
        # each conceptEntry can contain one or more langSec
        lang_dicts = []
        for lang_item in concept['langSec']:
            lang = lang_item['lang']
            langs.add(lang)
            lang_dict = {'lang': lang}
            descripGrp = lang_item.get('descripGrp', None)
            if descripGrp:
                descrip = descripGrp.get('descrip', None)
                if descrip:
                    definition = descrip.get('definition', None)
                    if definition:
                        definition = join_blankspaces(definition)
                        lang_dict['definition'] = definition
                        columns.add('definition')
                admin = descripGrp.get('admin', None)
                if admin:
                    source = admin.get('source', None)
                    if source:
                        # lang_dict['source'] = source
                        lang_dict['def_source'] = source
                        columns.add('def_source')
            # each langSec can contain one or more termSec
            term_items = lang_item['termSec']
            if not type(term_items) == list:
                term_items = [term_items]
            term_dicts = []
            for term_item in term_items:
                term_dict = {'term': term_item['term']}
                termType = term_item.get('termType', None)
                if termType:
                    # term_dict['termType'] = termType
                    term_dict['type'] = termType
                    columns.add('type')
                partOfSpeech = term_item.get('partOfSpeech', None)
                if partOfSpeech:
                    # term_dict['partOfSpeech'] = partOfSpeech
                    term_dict['POS'] = partOfSpeech
                    columns.add('POS')
                reliabilityCode = term_item.get('reliabilityCode', None)
                if reliabilityCode:
                    # term_dict['reliabilityCode'] = reliabilityCode
                    term_dict['reliability'] = reliabilityCode
                    columns.add('reliability')
                administrativeStatus = term_item.get('administrativeStatus', None)
                if administrativeStatus:
                    # term_dict['administrativeStatus'] = administrativeStatus
                    term_dict['status'] = administrativeStatus.replace('Term-admn-sts', '')
                    columns.add('status')
                # each termSec can contain one or more termNote
                term_notes = term_item.get('termNote', [])     
                if term_notes and not type(term_notes) == list:
                    term_notes = [term_notes]
                for term_note in term_notes:
                    partOfSpeech = term_note.get('partOfSpeech', None)
                    if partOfSpeech:
                        # term_dict['partOfSpeech'] = partOfSpeech
                        term_dict['POS'] = partOfSpeech
                        columns.add('POS')
                    termType = term_note.get('termType', None)
                    if termType:
                        # term_dict['termType'] = termType
                        term_dict['type'] = termType
                        columns.add('type')
                    administrativeStatus = term_note.get('administrativeStatus', None)
                    if administrativeStatus:
                        # term_dict['administrativeStatus'] = administrativeStatus.replace('Term-admn-sts', '')
                        term_dict['status'] = administrativeStatus.replace('Term-admn-sts', '')
                        columns.add('status')
                # each termSec can contain zero, one or more (?) descrip items
                term_descrips = term_item.get('descrip', [])
                if term_descrips and not type(term_descrips) == list:
                    term_descrips = [term_descrips]
                for term_descrip in term_descrips:
                    reliabilityCode = term_descrip.get('reliabilityCode', None)
                    if reliabilityCode:
                        # term_dict['reliabilityCode'] = reliabilityCode
                        term_dict['reliability'] = reliabilityCode
                        columns.add('reliability')
                # each termSec can contain zero or one descripGrp
                descripGrp = term_item.get('descripGrp', None)     
                if descripGrp:
                    descrip = descripGrp.get('descrip', None)
                    if descrip:
                        context = descrip.get('context', None)
                        if context:
                            context = join_blankspaces(context)
                            term_dict['context'] = context
                            columns.add('context')
                    admin = descripGrp.get('admin', None)
                    if admin:
                        source = admin.get('source', None)
                        if source:
                            # term_dict['source'] = source
                            term_dict['term_source'] = source
                            columns.add('term_source')
                term_dicts.append(term_dict)
            lang_dict['termSec'] = term_dicts
            lang_dicts.append(lang_dict)
        lang_dicts.sort(key=lambda x: x['lang'])
        concept_dict['langSec'] = lang_dicts
        concept_dicts.append(concept_dict)
    langs = sorted(list(langs))
    concept_columns = [c for c in ALL_CONCEPT_COLUMNS if c in columns]
    lang_columns = [c for c in ALL_LANG_COLUMNS if c in columns]
    term_columns = [c for c in ALL_TERM_COLUMNS if c in columns]
    return {'tbx': {'text': {'index': {'langs': langs, 'conceptColumns': concept_columns, 'langColumns': lang_columns, 'termColumns': term_columns,}, 'body': {'conceptEntry': concept_dicts}}}}

def tbx_dict_2_tsv(tbx_dict: dict) -> str:
    """
    Takes a Python dict representing an xml-tbx document parsed with tbx_xml_2_dict, simpliflied but enriched with an 'index' section.
    Produces a text file in TSV format (tab-separated values), whose columns are specified by the 'index' section.
    """
    text = tbx_dict['tbx']['text']
    index = text['index']
    concept_columns = index['conceptColumns']
    concept_blanks = ['' for key in concept_columns]
    lang_columns = index['langColumns']
    lang_blanks = ['' for key in lang_columns]
    term_columns = index['termColumns']
    # builds the heading row
    col_names = concept_columns + lang_columns + term_columns
    headings = '\t'.join(col_names).replace('def_source', 'source').replace('term_source', 'source')
    lines = [headings]
    # loops on the concept list
    for concept_dict in text['body']['conceptEntry']:
        concept_values = [concept_dict.get(key, '') for key in concept_columns]
        # loops on the language list
        lang_dicts = concept_dict['langSec']
        i_lang = 0
        for lang_dict in concept_dict['langSec']:
            lang_values = [lang_dict.get(key, '') for key in lang_columns]
            # loops on the term list
            i_term = 0
            for term_dict in lang_dict['termSec']:
                values = []
                term_values = [term_dict.get(key, '') for key in term_columns]
                if i_lang == 0 and i_term == 0:
                    values += concept_values
                else:
                    values += concept_blanks
                if i_term == 0:
                    values += lang_values
                else:
                    values +=lang_blanks
                values += term_values
                lines.append('\t'.join(values))
                i_term += 1 
            i_lang += 1
    csv_data = '\n'.join(lines)
    return csv_data

def tbx_tsv_2_dict(tsv_data: str) -> dict:
    lines = tsv_data.splitlines()
    reader = csv.reader(lines, delimiter='\t')
    parsed_tsv = list(reader)
    columns = parsed_tsv[0]
    i_term = None
    for index, col in enumerate(columns):
        if col == 'term':
            i_term = index
        elif col == 'source':
            columns[index] = i_term and 'term_source' or 'def_source'
    rows = parsed_tsv[1:]
    row_dicts = []
    for row in rows:
        row_dicts.append(dict(zip(columns, row)))
    langs = set()
    for d in row_dicts:
        if d['lang']:
            langs.add(d['lang'])
    langs = sorted(list(langs))
    concept_columns = [c for c in ALL_CONCEPT_COLUMNS if c in columns]
    lang_columns = [c for c in ALL_LANG_COLUMNS if c in columns]
    term_columns = [c for c in ALL_TERM_COLUMNS if c in columns]
    row_dicts.reverse()
    concept_dicts = []
    lang_dicts = []
    term_dicts = []
    for row in row_dicts:
        term_dict = {}
        for c in term_columns:
            if row[c]:
                term_dict[c] = row[c]
        term_dicts.append(term_dict)
        if row['lang']:
            lang_dict = {}
            for c in lang_columns:
                if row[c]:
                    lang_dict[c] = row[c]
            term_dicts.reverse()
            lang_dict['termSec'] = term_dicts
            term_dicts = []
            lang_dicts.append(lang_dict)
        if row['id']:
            concept_dict = {}
            for c in concept_columns:
                if row[c]:
                    if c == 'subjects':
                        concept_dict[c] = [row[c]]
                    else:
                        concept_dict[c] = row[c]
            lang_dicts.reverse()
            concept_dict['langSec'] = lang_dicts
            lang_dicts = []
            concept_dicts.append(concept_dict)
    concept_dicts.reverse()
    tbx_dict = {'tbx': {'text': {'index': {'langs': langs, 'conceptColumns': concept_columns, 'langColumns': lang_columns, 'termColumns': term_columns,}, 'body': {'conceptEntry': concept_dicts}}}}
    return tbx_dict

def add_key_val_to_xml(parent, key, val):
    """ add_key_val_to_xml
    this recursive function converts and appends a sub-tree
    """
    key = TBX_DICT_2_XML_MAP.get(key, key)
    if type(val) is dict:
        child = Element(key)
        parent.append(child)
        for k, v in val.items():
            add_key_val_to_xml(child, k, v)
    elif type(val) is list:
        for item in val:
            add_key_val_to_xml(parent, key, item)
    else:
        inner_tag = None
        child = None
        val = str(val)
        splitted_key = key.split(' ')
        if len(splitted_key) == 2: # 2 nested elements?
            wrapper_tag = splitted_key[0]
            inner_key = splitted_key[1]
            wrapper = parent.find(wrapper_tag)
            if not wrapper:
                wrapper = Element(wrapper_tag)
                parent.append(wrapper)
            parent = wrapper
            key = inner_key
        splitted_key = key.split('-')
        if len(splitted_key) == 2: # element (?) with attribute?
            inner_tag = splitted_key[0]
            attr = splitted_key[1]
            if inner_tag:
                child = Element(inner_tag, type=attr)
            else:
                parent.set(attr, val)
        else:
            child = Element(key)
        if child is not None:
            child.text = val
            parent.append(child)

def tbx_dict_2_xml(tbx_dict: dict) -> str:
    """
    Build in memory an etree (XML) object by converting a Python dict
    which represents a TBX document with simplified syntax 
    """
    xml_str = """<?xml version="1.0" encoding="utf-8"?>
<tbx type="TBX-Basic" style="dca" xml:lang="en" xmlns="urn:iso:std:iso:30042:ed-2">
    <text>
        {}
    </text>
</tbx>
"""
    block_list = []
    body = Element('body')
    for concept_entry in tbx_dict['tbx']['text']['body']['conceptEntry']:
        add_key_val_to_xml(body, 'conceptEntry', concept_entry)
    xml_block = tostring(body, encoding="unicode")
    block_list.append(xml_block)
    return xml_str.format('\n'.join(block_list))

def tbx_xml_to_json_file(path: str, filename: str) -> None:
    """ tbx_xml_to_json_file
    Reads from file and parses an xml string in TBX format.
    Converts to JSON the parsed object.
    Removes some syntax derived from xml.
    Writes the result string to a .json file in the same folder.
    """
    tbx_filename = os.path.join(path, filename+'.tbx')
    json_filename = os.path.join(path, filename+'.json')
    tbx_str = read_input_file(tbx_filename)
    json_str = json.dumps(tbx_xml_2_dict(tbx_str, split_subjects=True))
    write_output_file(json_filename, json_str)

def tbx_xml_to_csv_file(path: str, filename: str) -> None:
    """ tbx_xml_to_csv_file
    Reads from file and parses an xml string in TBX format.
    Converts to JSON the parsed object.
    Removes some syntax derived from xml.
    Converts JSON to CSV (with tab separated values)
    Writes the result string to a .csv file in the same folder.
    """
    tbx_filename = os.path.join(path, filename+'.tbx')
    csv_filename = os.path.join(path, filename+'.csv')
    tbx_str = read_input_file(tbx_filename)
    tbx_dict = tbx_xml_2_dict(tbx_str)
    csv_str = tbx_dict_2_tsv(tbx_dict)
    write_output_file(csv_filename, csv_str)

def tbx_csv_to_json_file(path: str, filename: str) -> None:
    """ tbx_csv_to_json_file
    Reads a CSV file (with tab separated values) and parses it to a list of lists.
    First row contains a list of TBX field names related to concept, language and term in the order.
    Parse the other rows, in reverse order, to reconstruct term, language and concept sub-dicts.
    Writes the resulting dict as a file in JSON format in the same folder.
    """
    csv_filename = os.path.join(path, filename+'.csv')
    json_filename = os.path.join(path, filename+'.json')
    tsv_data = read_input_file(csv_filename)
    tbx_dict = tbx_tsv_2_dict(tsv_data)
    json_str = json.dumps(tbx_dict)
    write_output_file(json_filename, json_str)

def tbx_csv_to_xml_file(path: str, filename: str) -> None:
    """ tbx_csv_to_xml_file
    Reads a CSV file (with tab separated values) and parses it to a list of lists.
    First row contains a list of TBX field names related to concept, language and term in the order.
    Parse the other rows, in reverse order, to reconstruct term, language and concept sub-dicts.
    Convert the resulting dict to an xml object in memory and then linearizes it as an XML file of TBX extension.
    """
    csv_filename = os.path.join(path, filename+'.csv')
    tbx_filename = os.path.join(path, filename+'.tbx')
    tsv_data = read_input_file(csv_filename)
    tbx_dict = tbx_tsv_2_dict(tsv_data)
    xml_str = tbx_dict_2_xml(tbx_dict)
    write_output_file(tbx_filename, xml_str)

def tbx_json_to_xml_file(path: str, filename: str) -> None:
    """ tbx_json_to_xml_file
    Reads a JSON file that represents a TBX document with simplified syntax and convert it to a Python dict.
    Build in memory an etree (XML) object by converting the Python dict.
    Convert the Python dict to an xml object in memory and then linearizes it as an XML file of TBX extension.
    """
    json_filename = os.path.join(path, filename+'.json')
    tbx_filename = os.path.join(path, filename+'.tbx')
    json_str = read_input_file(json_filename)
    tbx_dict = json.loads(json_str)
    xml_str = tbx_dict_2_xml(tbx_dict)
    write_output_file(tbx_filename, xml_str)
