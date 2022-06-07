# Name: Hylke Brouwer, Collin Krooneman, Maurice Voors
# Date: 7-6-2022
# File: wiki_link_system.py
# Description

import os
import sys
import csv
import spacy
from re import search
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
from nltk.wsd import lesk
from nltk.parse import CoreNLPParser
from mediawiki import MediaWiki
from pywsd.lesk import simple_lesk, adapted_lesk, cosine_lesk


def gpe_disambiguation(token):
    """Disambiguate between cities and countries"""

    with open('GPE/countries.txt') as countryFile:
        for line in countryFile:
            if token in line:
                return 'COU'
    with open('GPE/cities.txt', encoding='utf-8') as cityFile:
        csvReader = csv.reader(cityFile, delimiter=",")
        for line in csvReader:
            if token in line[1] or token in line[2]:
                return 'CIT'
    return 'COU'


def cleanup_list(data_list):
    """Removes newline characters from list items and looks for
    empty strings in the list and removes them as well
    """
    data = []
    for content in data_list:
        if "\n" in content:
            no_newline = content.strip("\n")
            data.append(no_newline)
        else:
            data.append(content)
    while ("" in data):
        data.remove("")
    return data


def find_search_term(file_cont, current_word, search_list):
    word_columns = current_word.split()
    next_w_i = file_cont.index(current_word) + 1
    next_word = file_cont[next_w_i]
    next_word_col = file_cont[next_w_i].split()
    search_list = search_list + [word_columns[3]]
    if len(next_word_col) != 6:
        return search_list
    elif word_columns[5] != next_word_col[5]:
        return search_list
    elif next_word == file_cont[-1]:
        search_list = search_list + [next_word_col[3]]
        return search_list
    else:
        return find_search_term(file_cont, next_word, search_list)


def create_tokens_corenlp(lines):
    """Creates tokens and tags using CoreNLP"""
    ner_tagger = CoreNLPParser(url='http://localhost:9000', tagtype='ner')

    # this removes the dash character to prevent multi-token words
    new_lines = []
    for line in lines:
        if "-" in line[3] and len(line[3]) > 1:
            new_word = line[3].replace("-", '')
            new_line = line[0], line[1], line[2], new_word, line[4]
            new_lines.append(new_line)
        else:
            new_lines.append(line)

    tokens = [line[3] for line in new_lines]
    entity_tokens = ner_tagger.tag(tokens)

    return tokens, entity_tokens, lines


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


def spacy_tagger(raw):
    """Finds named entities based on SpaCy model
    and return these entities
    """
    new_entities = []
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(raw)
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


def print_to_files(lines, entities, dir, content):
    """Prints the output to designated folder"""
    for line in lines:
        line_str = ' '.join(line)
        presence = False
        for entity in entities:
            if line[0] == entity[0] and line[1] == entity[1]:
                presence = True
                saved_ent = entity[3]
        if presence:
            for cont in content:
                if type(cont) != list:
                    cont = list(cont)
                cont_split = cont
                wiki_url = cont_split[-1]
                if line[0] == cont_split[0] and line[1] == cont_split[1]:
                    with open(os.path.join(sys.argv[1], dir, "test.txt"), "a") as f:
                        full_line = line_str + " " + saved_ent + " " + wiki_url + "\n"
                        f.write(full_line)
        else:
            with open(os.path.join(sys.argv[1], dir, "test.txt"), "a") as f:
                full_line = line_str + "\n"
                f.write(full_line)


def main():

    dir_names = os.listdir(sys.argv[1])
    dir_names_sorted = sorted(dir_names)
    dir_count = 1
    dir_total = len(dir_names)
    for dir in dir_names_sorted:
        with open(os.path.join(sys.argv[1], dir, "en.tok.off.pos"), "r") as f:
            file_content = f.readlines()

        # this prints the progress to the terminal
        print(f">>> Directory {dir_count}/{dir_total} is being processed...")

        lines = [line.rstrip().split() for line in file_content]
        token_doc = ' '.join(line[3] for line in lines)
        entities = []

        tokens, entity_tokens, n_lines = create_tokens_corenlp(lines)

        # find entities using Stanford CoreNLP NER tagger
        coreNLP_entity = corenlp_ner_tagger(tokens, entity_tokens, n_lines)
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

        # find entities using NLTK WordNet
        wn_entity = categorise_wordnet(lines, token_doc)
        if wn_entity:
            entities.append(wn_entity)
        print(">>>>>> WordNet tagging is done")


        # this section below is code related to wikipedia

        # entity_cont = []
        # sentence = []
        # sentence_wdata = []
        complete_cont = []

        wikipedia = MediaWiki()

        # new_lines = []
        # for line in n_lines:
        #     if "-" in line[3] and len(line[3]) > 1:
        #         new_word = line[3].replace("-", '')
        #         new_line = line[0], line[1], line[2], new_word, line[4]
        #         new_lines.append(new_line)
        #     else:
        #         new_lines.append(line)


        # for word_data in new_lines:
        #     sentence_wdata.append(word_data)
        #     if len(word_data) > 4:
        #         sentence.append(word_data[3])

        # empty_items = 0
        # for item in sentence_wdata:
        #     if len(item) < 5:
        #         empty_items += 1

        # for sent_i in range(len(sentence_wdata) - empty_items):
        #     data_c = sentence_wdata[sent_i]
        #     if type(data_c) != list:
        #         data_c = list(data_c)
        #     # print(entity_tokens[sent_i][1][:3])
        #     if entity_tokens != "O":
        #         data_c.append(entity_tokens)
        #     entity_cont.append(data_c)

        print(">>>>>> Wikipedia search is starting")
        j = 0
        while j < len(entities): # try this with the entities variable
            word_info = entities[j]
            info_col = word_info
            if len(info_col) == 6:
                if word_info != entities[-1]:
                    search_for = find_search_term(entities, word_info, [])
                else:
                    if len(entities[j - 1].split()) == 6:
                        search_for = find_search_term(entities, entities[j - 1], [])
                search_results = wikipedia.search(" ".join(search_for))
                try:
                    wiki_page = wikipedia.page(search_results[0])
                    wikip_url = wiki_page.url
                except:
                    wikip_url = "ERROR_OCCURED"
                info_col.append(wikip_url)
                if word_info != entities[-1]:
                    for l in range(len(search_for)):
                        columns = entities[j + l].split()
                        columns.append(wikip_url)
                        complete_cont.append(" ".join(columns))
                j += len(search_for)
            else:
                j += 1
                complete_cont.append(word_info)

        print(">>>>>> Wikipedia search is done")

        print_to_files(lines, entities, dir, complete_cont)

        print(f'>>> Directory {dir_count}/{dir_total} is done')
        dir_count += 1


if __name__ == "__main__":
    main()
