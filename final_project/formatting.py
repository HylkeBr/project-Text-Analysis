import sys
import os


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

def ID_data(data_list):
    """Assigns an ID to every item and filters out the 
    information that is not that important. Returns dict
    (key = ID, value = data)"""
    id_data = {}
    i = 0
    for data_item in data_list:
        id_data[i] = data_item.split()[3:]
        i += 1
    
    usefull_id_data = {}
    for k, v in id_data.items():
        if len(v) > 2:
            usefull_id_data[k] = v
    
    return usefull_id_data


def mk_dict(filenames, directory):
    """Opens files and puts their content in a dict, with the 
    filename as key and it's content as value."""
    cont_dict = {}
    for filename in filenames:
        for file in os.listdir(directory):
            if filename in file:
                with open(os.path.join(directory, file), "r") as f:
                    files_content = f.readlines()
        cont_dict[filename] = cleanup_list(files_content)
    
    return cont_dict


def find_annotations(filenames, dict_A, dict_B):
    """Returns a dict with the data from annotater A and B that were
    annotated by both annotaters. The values of those items were put in
    a list."""
    agreed_list_A = []
    agreed_list_B = []
    column_six_A = []
    column_six_B = []
    column_seven_A = []
    column_seven_B = []
    right_link_A = []
    right_link_B = []
    
    for fileID in filenames:
        datafile_A = dict_A[fileID]
        datafile_B = dict_B[fileID]
        for i in range(len(datafile_A)):
            word_data_A = datafile_A[i].split()
            word_data_B = datafile_B[i].split()
            if len(word_data_A) >= 6:
                column_six_A.append(True)
                if len(word_data_B) >= 6:
                    agreed_list_A.append(word_data_A[5])
                    agreed_list_B.append(word_data_B[5])
            else:
                column_six_A.append(False)
            if len(word_data_B) >= 6:
                column_six_B.append(True)
            else:
                column_six_B.append(False)

            if len(word_data_A) >= 7:
                column_seven_A.append(True)
            else:
                column_seven_A.append(False)
            if len(word_data_B) >= 7:
                column_seven_B.append(True)
            else:
                column_seven_B.append(False)
            
            # Every link there is in dataset B (seventh column) is right, because
            # of it being the "answers" dataset
            if len(word_data_B) >= 7:
                right_link_B.append(True)
            else:
                right_link_B.append(False)
            if len(word_data_A) >= 7 and len(word_data_B) >= 7:
                if word_data_A[6] == word_data_B[6]:
                    right_link_A.append(True)
                else:
                    right_link_A.append(False)
            else:
                right_link_A.append(False)
    
    agreed_dict = {
        "data_A" : agreed_list_A,
        "data_B" : agreed_list_B,
        "column_six_A" : column_six_A,
        "column_six_B" : column_six_B,
        "column_seven_A" : column_seven_A,
        "column_seven_B" : column_seven_B,
        "right_link_A" : right_link_A,
        "right_link_B" : right_link_B
    }

    return agreed_dict


def main():
    filenames = ["d0071", "d0076", "d0112", "d0117", "d0195", "d0271", "d0315", "d0337",
    "d0527", "d0577", "d0583", "d0592", "d0616", "d0622", "d0653", "d0675", "d0688", "d0691"]

    cont_dict_A = mk_dict(filenames, sys.argv[1])
    cont_dict_B = mk_dict(filenames, sys.argv[2])
    
    ann = find_annotations(filenames, cont_dict_A, cont_dict_B)

    print("Amount of words both annotaters annotated:")
    print(len(ann["data_A"]))
    print()
    print("Annotated data annotater A:")
    print(ann["data_A"])
    print()
    print("Annotated data annotater B:")
    print(ann["data_B"])


if __name__ == "__main__":
    main()