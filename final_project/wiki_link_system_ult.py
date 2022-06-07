# Name: Hylke Brouwer, Collin Krooneman, Maurice Voors
# Date: 7-6-2022
# File: wiki_link_system.py
# This program takes a folder of directories containing a POS-tagged corpus
# which is annotated by giving specified classes as well as wikipedia urls

import os
import sys
import csv
import spacy
from distutils.log import info
from re import search
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
from nltk.wsd import lesk
from nltk.parse import CoreNLPParser
from mediawiki import MediaWiki
from pywsd.lesk import simple_lesk, adapted_lesk, cosine_lesk


def create_tokens_corenlp(lines):
    """Creates tokens based on given lines
    and tags using CoreNLP
    """
    ner_tagger = CoreNLPParser(url='http://localhost:9000', tagtype='ner')

    # remove cases that would create multi-tokens
    new_lines = clean_lines(lines)

    tokens = [line[3] for line in new_lines]
    entity_tokens = ner_tagger.tag(tokens)

    return tokens, entity_tokens


def clean_lines(lines):
    """Removes specific characters from given corpus"""
    new_lines = []
    for line in lines:
        if "-" in line[3] and len(line[3]) > 1:
            new_word = line[3].replace("-", '')
            new_line = line[0], line[1], line[2], new_word, line[4]
            new_lines.append(new_line)
        else:
            new_lines.append(line)

    newer_lines = []
    for line in new_lines:
        if "," in line[3] and len(line[3]) > 1:
            new_word = line[3].replace(",", '')
            new_line = line[0], line[1], line[2], new_word, line[4]
            newer_lines.append(new_line)
        else:
            newer_lines.append(line)

    more_lines = []
    for line in new_lines:
        if "'" in line[3] and len(line[3]) > 1:
            new_word = line[3].replace("'", '')
            new_line = line[0], line[1], line[2], new_word, line[4]
            more_lines.append(new_line)
        else:
            more_lines.append(line)

    even_more_lines = []
    for line in more_lines:
        if line[3].endswith('.') and len(line[3]) > 1:
            replace = line[3]
            new_word = replace[:-1]
            new_line = line[0], line[1], line[2], new_word, line[4]
            even_more_lines.append(new_line)
        else:
            even_more_lines.append(line)

    return even_more_lines


def corenlp_ner_tagger(tokens, entity_tokens, lines):
    """Finds named entities based on CoreNLP model
    and returns the entities
    """
    j = 0
    new_entities = []
    for i in range(len(tokens)):
        token = entity_tokens[j][0]
        nec = entity_tokens[j][1]
        if nec == 'PERSON':
            new_entities.append((lines[i][0], lines[i][1], token, 'PER'))
        elif nec == 'ORGANIZATION':
            new_entities.append((lines[i][0], lines[i][1], token, 'ORG'))
        elif nec == 'COUNTRY' or nec == 'STATE_OR_PROVINCE':
            new_entities.append((lines[i][0], lines[i][1], token, 'COU'))
        elif nec == 'CITY':
            new_entities.append((lines[i][0], lines[i][1], token, 'CIT'))
        j += 1

    return new_entities


def categorise_wordnet(lines, doc):
    """Finds named entities based on
    WordNet information and returns the entity
    """
    categories = {'ANI': ['animal', 'bird'], 'SPO': ['sport'],
                  'NAT': ['ocean', 'river', 'mountain', 'crack',
                          'land', 'forest', 'jungle', 'sea']}
    for line in lines:
        token = line[3]
        tag = line[4]
        if tag in ['NN', 'NNPS', 'NNS']:
            synsets = wordnet.synsets(token, pos=wordnet.NOUN)
            if len(synsets) > 1:
                synset = adapted_lesk(doc, token, pos='NOUN')
                hypernyms = [i for i in synset.closure(lambda s:s.hypernyms())]
                for hyp in hypernyms:
                    if str(hyp) != "Synset('public_transport.n.01')" and str(hyp) != "Synset('sports_equipment.n.01')":
                        for key, value_list in categories.items():
                            for cat in value_list:
                                if cat in str(hyp):
                                    return (line[0], line[1], token, key)


def spacy_tagger(raw):
    """Finds named entities based on SpaCy model
    and return these entities
    """
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(raw)
    new_entities = []
    for ent in doc.ents:
        b = 0 + ent.start_char
        e = 0
        for entit in ent.text.split():
            e = b + len(entit)
            if ent.label_ not in ['NORP', 'EVENT', 'FAC', 'PRODUCT', 'LAW',
                                  'LANGUAGE', 'DATE', 'TIME', 'PERCENT',
                                  'MONEY', 'QUANTITY', 'ORDINAL', 'CARDINAL']:
                if ent.label_ in ['COU', 'GPE']:
                    label = gpe_disambiguation(ent.text)
                elif ent.label_ == 'PERSON':
                    label = 'PER'
                elif ent.label_ == 'LOC':
                    label = 'NAT'
                elif ent.label_ == 'WORK_OF_ART':
                    label = 'ENT'
                else:
                    label = ent.label_
                new_entities.append((str(b), str(e), entit, label))
            e += 1
            b = e

    return new_entities


def gpe_disambiguation(token):
    """Disambiguates between cities and countries
    based on given corpus containing tagged classes
    """
    with open('amb/countries.txt') as countryFile:
        for line in countryFile:
            if token in line:
                return 'COU'
    with open('amb/cities.txt', encoding='utf-8') as cityFile:
        csvReader = csv.reader(cityFile, delimiter=",")
        for line in csvReader:
            if token in line[1] or token in line[2]:
                return 'CIT'

    return 'COU'


def wiki_linker(entities):
    """Finds the wikipedia links
    of the tagged entities
    """
    wikipedia = MediaWiki()
    complete_cont = []
    j = 0
    while j < len(entities):
        info_col = entities[j]
        word_info = " ".join(info_col)
        if len(info_col) == 6:
            if info_col != entities[-1]:
                search_for = find_search_term(entities, word_info, [])
            else:
                if len(entities[j - 1]) == 6:
                    search_for = find_search_term(entities, entities[j - 1], [])
            search_results = wikipedia.search(" ".join(search_for))
            try:
                wiki_page = wikipedia.page(search_results[0])
                wikip_url = wiki_page.url
            except:
                wikip_url = "-"
            list(info_col).append(wikip_url)
            if word_info != entities[-1]:
                for k in range(len(search_for)):
                    columns = list(entities[j + k])
                    columns.append(wikip_url)
                    complete_cont.append(" ".join(columns))
            j += len(search_for)
        else:
            j += 1
            complete_cont.append(word_info)

    return complete_cont


def find_search_term(file_cont, current_word, search_list):
    """Returns search query based on given corpus
    containing tagged classes
    """
    if type(current_word) != list:
        word_columns = current_word.split()
    else:
        word_columns = current_word

    next_w_i = file_cont.index(word_columns) + 1
    next_word = file_cont[next_w_i]
    next_word_col = file_cont[next_w_i]
    search_list = search_list + [word_columns[3]]
    if len(next_word_col) != 6:
        return search_list
    elif word_columns[5] != next_word_col[5]:
        return search_list
    elif next_word == file_cont[-1]:
        return search_list
    else:
        return find_search_term(file_cont, next_word, search_list)


def make_full_doc(lines, entities):
    """Prints the output to designated folder"""
    full_doc = []
    for line in lines:
        line_str = ' '.join(line)
        presence = False
        for entity in entities:
            if line[0] == entity[0] and line[1] == entity[1]:
                presence = True
                saved_ent = entity[3]
        if presence:
            part_line = line_str.split()
            part_line.append(saved_ent)
            full_doc.append(part_line)
        else:
            full_line = line_str.split()
            full_doc.append(full_line)

    return full_doc


def print_to_files(full_doc, dir):
    """Writes first line to output file and
    appends remaining lines to the file
    """
    first = True
    file_name = "en.tok.off.pos.ent"
    for item in full_doc:
        if first:
            with open(os.path.join(sys.argv[1], dir, file_name), "w") as f:
                full_line = item + "\n"
                f.write(full_line)
            first = False
        else:
            with open(os.path.join(sys.argv[1], dir, file_name), "a") as f:
                full_line = item + "\n"
                f.write(full_line)


def main():

    dir_names = os.listdir(sys.argv[1])
    dir_names_sorted = sorted(dir_names)
    dir_count = 1
    dir_total = len(dir_names)

    for dir in dir_names_sorted:
        with open(os.path.join(sys.argv[1], dir, "en.tok.off.pos"), "r") as f:
            file_content = f.readlines()

        print(f">>> Directory {dir_count}/{dir_total} is being processed...")

        entities = []
        lines = [line.rstrip().split() for line in file_content]
        tokens, entity_tokens = create_tokens_corenlp(lines)
        token_doc = ' '.join(line[3] for line in lines)

        # find entities using Stanford CoreNLP NER tagger
        coreNLP_entity = corenlp_ner_tagger(tokens, entity_tokens, lines)
        if coreNLP_entity:
            for coreNLP_ent in coreNLP_entity:
                entities.append(coreNLP_ent)
        print(">>>>>> CoreNLP tagging is done")

        # find entities using SpaCy NER tagger
        spacy_entity = spacy_tagger(token_doc)
        if spacy_entity:
            for spacy_ent in spacy_entity:
                entities.append(spacy_ent)
        print(">>>>>> SpaCy tagging is done")

        # find entities using NLTK WordNet and hypernyms
        wn_entity = categorise_wordnet(lines, token_doc)
        if wn_entity:
            entities.append(wn_entity)
        print(">>>>>> WordNet tagging is done")

        # create full document with tagged classes
        full_doc = make_full_doc(lines, entities)

        # find wiki pages using MediaWiki
        complete_cont = wiki_linker(full_doc)
        print(">>>>>> Wikipedia search is done")

        print_to_files(complete_cont, dir)

        perc_done = dir_count / dir_total * 100
        perc_round = round(perc_done, 1)
        print(f'>>> Progress {perc_round}% ({dir_count}/{dir_total})')
        dir_count += 1


if __name__ == "__main__":
    main()
