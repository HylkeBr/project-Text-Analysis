import os
from re import search
import sys
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.parse import CoreNLPParser
# import wikipedia
from mediawiki import MediaWiki


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


def main():
    wikipedia = MediaWiki()

    content_dict = {}
    dir_names = os.listdir(sys.argv[1])
    for dir in dir_names:
        with open(os.path.join(sys.argv[1], dir, "en.tok.off.pos"), "r") as f:
            file_content = f.readlines()
        content_dict[dir] = cleanup_list(file_content)
    
    #############################################
    # ENTITY RECOGNITION + WIKI-LINK ASSIGNMENT #
    #############################################

    ner_tagger = CoreNLPParser(url="http://localhost:9000", tagtype="ner")
    entity_data = {}

    print("System started\n")
    print("Completion:")
    print(0.0, "%")
    files_done = 0

    for folder in dir_names:
    # ^ replace '["d0021"]' with 'for folder in dir_names:' for all files (et vice versa) ^ 

        entity_cont = []
        sentence = []
        sentence_wdata = []
        complete_cont = []

        file_cont = content_dict[folder]
        for word_data in file_cont:
            sentence_wdata.append(word_data)
            data_columns = word_data.split()
            if len(data_columns) > 4:
                sentence.append(data_columns[3])

        assigned_ent = ner_tagger.tag(sentence)

        # checks for items that do not have a word value
        empty_items = 0
        for item in sentence_wdata:
            if len(item.split()) < 5:
                empty_items += 1
        
        for sent_i in range(len(sentence_wdata) - empty_items):
            data_c = sentence_wdata[sent_i].split()
            if assigned_ent[sent_i][1][:3] != "O":
                data_c.append(assigned_ent[sent_i][1][:3])
            
            entity_cont.append(" ".join(data_c))

        j = 0
        while j < len(entity_cont):
            word_info = entity_cont[j]
            info_col = word_info.split()
            if len(info_col) == 6:
                if word_info != entity_cont[-1]:
                    search_for = find_search_term(entity_cont, word_info, [])
                else:
                    if len(entity_cont[j - 1].split()) == 6:
                        search_for = find_search_term(entity_cont, entity_cont[j - 1], [])
                search_results = wikipedia.search(" ".join(search_for))
                try:
                    wiki_page = wikipedia.page(search_results[0])
                    wikip_url = wiki_page.url
                except:
                    wikip_url = "ERROR_OCCURED"
                info_col.append(wikip_url)
                if word_info != entity_cont[-1]:
                    for l in range(len(search_for)):
                        columns = entity_cont[j + l].split()
                        columns.append(wikip_url)
                        complete_cont.append(" ".join(columns))
                j += len(search_for)
            else:
                j += 1
                complete_cont.append(word_info)

        entity_data[folder] = complete_cont

        # for giving a sence how long it has still to load
        
        sys.stdout.write("\033[F")
        sys.stdout.write("\033[K")
        perc_done = files_done / len(dir_names) * 100
        print(round(perc_done, 1), "%")
        files_done += 1


    # for showing the contents of entity_data better:
    for k, v in entity_data.items():
        print(k)
        print("________________________________________")
        print()
        for item in v:
            print(item)
        print()


if __name__ == "__main__":
    main()
