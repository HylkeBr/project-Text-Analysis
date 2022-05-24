import os
import sys
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.parse import CoreNLPParser
import wikipedia


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


def convert_POS(nltk_POS_tag):
    if "NN" in nltk_POS_tag:
        return "n"
    elif "JJ" in nltk_POS_tag:
        return "a"
    elif "RB" in nltk_POS_tag:
        return "r"
    elif "VB" in nltk_POS_tag:
        return "v"
    else:
        return False

def main():
    content_dict = {}
    dir_names = os.listdir(sys.argv[1])
    for dir in dir_names:
        with open(os.path.join(sys.argv[1], dir, "en.tok.off.pos"), "r") as f:
            file_content = f.readlines()
        content_dict[dir] = cleanup_list(file_content)
    
    ######################################
    # LEMMATIZATION & ENTITY RECOGNITION #
    ######################################

    lemmatizer = WordNetLemmatizer()
    ner_tagger = CoreNLPParser(url="http://localhost:9000", tagtype="ner")

    entity_data = {}
    new_file_cont = []
    for folder in ["d0021"]:
    # ^ replace with 'for folder in dir_names:' for all files ^

        #print()
        #print(folder)
        #print("_______________________________________________")
        #print()
        file_cont = content_dict[folder]
        for word_data in file_cont:
            data_columns = word_data.split()
            if len(data_columns) > 4:
                if convert_POS(data_columns[4]) == False:
                    word_lemma = lemmatizer.lemmatize(data_columns[3])
                else:
                    word_lemma = lemmatizer.lemmatize(data_columns[3], pos=convert_POS(data_columns[4]))
                entity = ner_tagger.tag([word_lemma])
                if entity[0][1] != "O":
                    data_columns.append(entity[0][1][:3])

                #new_file_cont.append(" ".join(data_columns))
            
            if len(data_columns) == 6:
                #print(wikipedia.search(word_lemma))
                if len(wikipedia.search(word_lemma)) != 0:
                    wikipages = wikipedia.search(word_lemma)
                    print(wikipedia.page(wikipages[0]).url)
                    print()
                    data_columns.append(wikipedia.page(wikipages[0]).url)
            
            new_file_cont.append(" ".join(data_columns))

        entity_data[folder] = new_file_cont

    for k, v in entity_data.items():
        print(k)
        print()
        print(v)
        print()





if __name__ == "__main__":
    main()