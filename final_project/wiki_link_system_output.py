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
    '''Disambiguate between cities and countries'''
    with open('GPE/countries.txt') as countryFile:
        for line in countryFile:
            if token in line:
                return 'COU'
    with open('GPE/cities.txt', encoding='utf-8') as cityFile:
        csvReader = csv.reader(cityFile, delimiter=",")
        for line in csvReader:
            if token in line[1] or token in line[2]: #lowercase and uppercase city names
                return 'CIT'
    return 'COU'


def cleanup_list(data_list):
    """Removes newline characters from list items and looks for 
    empty strings in the list and removes them as well"""
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


def corenlp_ner_tagger(lines):
    new_entities = []
    ner_tagger = CoreNLPParser(url='http://localhost:9000', tagtype='ner')
    
    # This removes the dash character to prevent multi-token words
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
    print(entity_tokens)
    j = 0
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
    '''find named entities based on SpaCy model and return these entities'''
    
    new_entities = []
    nlp = spacy.load("en_core_web_sm")
    # create nlp pipeline
    doc = nlp(raw)
    # append entity offsets, text and tagged category
    for ent in doc.ents:

        # offsets have been adjusted to fit both double entities and single
        b = 0 + ent.start_char
        e = 0
        # (125, 132, 'Benazir', 'PER'), (133, 139, 'Bhutto', 'PER')
        for entit in ent.text.split():
            e = b + len(entit)
            # change SpaCy tags to our category tags
            if ent.label_ not in ['NORP', 'EVENT', 'FAC', 'PRODUCT', 'LAW',
                                  'LANGUAGE', 'DATE', 'TIME', 'PERCENT',
                                  'MONEY', 'QUANTITY', 'ORDINAL', 'CARDINAL']:

                # NORP = 'Israeli' police, 'Muslim' people etc.
                # if we tag NORP as ORG, the data shows that it is correct 14 times and incorrect 71 times, so let's not include
                # if ent.label_ == 'NORP':
                #     label = 'EXTRA'
                if ent.label_ in ['COU', 'GPE']: # Countries, cities, states.
                    # disambiguate between countries and cities
                    label = gpe_disambiguation(ent.text)
                elif ent.label_ == 'PERSON': # change PERSON to PER
                    label = 'PER'
                elif ent.label_ == 'LOC': # Non-GPE locations, mountain ranges, bodies of water.
                    label = 'NAT'
                elif ent.label_ == 'WORK_OF_ART': # Titles of books, songs, etc.
                    label = 'ENT'
                else:
                    label = ent.label_

                new_entities.append((str(b), str(e), entit, label))
            # for ent offsets
            e += 1
            b = e

    return new_entities


def categorise_wordnet(lines, doc):
    '''Finds named entities based on
    WordNet information and returns the entity'''
    categories = {'ANI': ['animal', 'bird'], 'SPO': ['sport'],
                  'NAT': ['ocean', 'river', 'mountain', 'crack',
                          'land', 'forest', 'jungle', 'sea']}
    for line in lines:
        token = line[3]
        tag = line[4]
        if tag in ['NN', 'NNPS', 'NNS']:
            synsets = wordnet.synsets(token, pos=wordnet.NOUN) # creates a list with all found synsets for noun
            if len(synsets) > 1:
                #use any of the following Lesk-based algorithms to disambiguate synset
                #so far adapted_lesk is the best: does not tag 'bird(s)', services' & 'workers', but does tag 'soldiers' and 'survivors' 
                synset = adapted_lesk(doc, token, pos='NOUN') # simple_lesk(), cosine_lesk(), adapted_lesk() or just lesk() from NLTK
                #find hypernyms for this synset
                hypernyms = [i for i in synset.closure(lambda s:s.hypernyms())] 
                #iterate through hypernyms to see whether they match a category
                for hyp in hypernyms:
                    if str(hyp) != "Synset('public_transport.n.01')" and str(hyp) != "Synset('sports_equipment.n.01')": # beide is geen sport
                        for key, value_list in categories.items():  
                            for cat in value_list:
                                if cat in str(hyp):
                                    return (line[0], line[1], token, key)


def print_to_files(lines, entities, dir):
    """Prints the output to designated folder"""
    for line in lines:
        part = ' '.join(line)
        presence = False
        for entity in entities:
            if line[0] == entity[0] and line[1] == entity[1]:
                presence = True
                saved = entity[3]
        if presence:
            with open(os.path.join(sys.argv[1], dir, "test.txt"), "a") as f:
                full = part + " " + saved + "\n"
                f.write(full)
        else:
            with open(os.path.join(sys.argv[1], dir, "test.txt"), "a") as f:
                full = part + "\n"
                f.write(full)


def main():

    # wikipedia = MediaWiki()
    # content_dict = {}

    dir_names = os.listdir(sys.argv[1])
    dir_names_sorted = sorted(dir_names)
    for dir in dir_names_sorted:
        with open(os.path.join(sys.argv[1], dir, "en.tok.off.pos"), "r") as f:
            file_content = f.readlines()

        print(dir)

        lines = [line.rstrip().split() for line in file_content]
        token_doc = ' '.join(line[3] for line in lines)
        entities = []
            
        # Find entities using Stanford CoreNLP NER tagger
        coreNLP_entity = corenlp_ner_tagger(lines)
        if coreNLP_entity:
            # print('Appending CoreNLP tagged entities', coreNLP_entity)
            for coreNLP_ent in coreNLP_entity:
                entities.append(coreNLP_ent)

        # Find entities using SpaCy NER tagger
        spacy_entity = spacy_tagger(token_doc) # a list of entities
        if spacy_entity: 
            # print('Appending SpaCy tagged entities', spacy_entity)
            for spacy_ent in spacy_entity:
                entities.append(spacy_ent)
        
        # find entities using NLTK WordNet
        wn_entity = categorise_wordnet(lines, token_doc)
        if wn_entity:
            # print('Appending WordNet tagged entities', wn_entity)
            entities.append(wn_entity)

        print_to_files(lines, entities, dir)

        #content_dict[dir] = cleanup_list(file_content)
        #print(content_dict)
    
    #############################################
    # ENTITY RECOGNITION + WIKI-LINK ASSIGNMENT #
    #############################################

    #ner_tagger = CoreNLPParser(url="http://localhost:9000", tagtype="ner")
    #entity_data = {}

    #print("System started\n")
    #print("Completion:")
    #print(0.0, "%")
    #files_done = 0

    #for folder in dir_names:
    # ^ replace '["d0021"]' with 'for folder in dir_names:' for all files (et vice versa) ^ 

      #  entity_cont = []
     #   sentence = []
     #   sentence_wdata = []
     #   complete_cont = []

        #file_cont = content_dict[folder]
       # for word_data in file_cont:
        #    sentence_wdata.append(word_data)
          #  data_columns = word_data.split()
        #    if len(data_columns) > 4:
        #        sentence.append(data_columns[3])
        

        #assigned_ent = ner_tagger.tag(sentence)
        #print(assigned_ent)

        # checks for items that do not have a word value
        #empty_items = 0
        #for item in sentence_wdata:
            #if len(item.split()) < 5:
                #empty_items += 1
        
        #for sent_i in range(len(sentence_wdata) - empty_items):
            #data_c = sentence_wdata[sent_i].split()
            #if assigned_ent[sent_i][1][:3] != "O":
                #data_c.append(assigned_ent[sent_i][1][:3])
            
            #entity_cont.append(" ".join(data_c))

        #j = 0
        #while j < len(entity_cont):
            #word_info = entity_cont[j]
            #info_col = word_info.split()
            #if len(info_col) == 6:
                #if word_info != entity_cont[-1]:
                    #search_for = find_search_term(entity_cont, word_info, [])
                #else:
                    #if len(entity_cont[j - 1].split()) == 6:
                        #search_for = find_search_term(entity_cont, entity_cont[j - 1], [])
                #search_results = wikipedia.search(" ".join(search_for))
                #try:
                   # wiki_page = wikipedia.page(search_results[0])
                    #wikip_url = wiki_page.url
               # except:
                    #wikip_url = "ERROR_OCCURED"
                #info_col.append(wikip_url)
                #if word_info != entity_cont[-1]:
                    #for l in range(len(search_for)):
                       # columns = entity_cont[j + l].split()
                        #columns.append(wikip_url)
                       # complete_cont.append(" ".join(columns))
               # j += len(search_for)
           # else:
               # j += 1
               # complete_cont.append(word_info)

       # entity_data[folder] = complete_cont

        # for giving a sence how long it has still to load
        
       # sys.stdout.write("\033[F")
       # sys.stdout.write("\033[K")
      #  perc_done = files_done / len(dir_names) * 100
       # print(round(perc_done, 1), "%")
       # files_done += 1


    # for showing the contents of entity_data better:
   # for k, v in entity_data.items():
       # print(k)
       # print("________________________________________")
       # print()
       # for item in v:
           # print(item)
       # print()


if __name__ == "__main__":
    main()
