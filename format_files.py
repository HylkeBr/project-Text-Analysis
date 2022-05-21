# name: Hylke Brouwer (s4953525)
# file: format_files.py
# date: 21-05-'22
# code: Formats files into right format. 
#           usage: python3 format_files.py <directory>
#           <directory> has to be a directory with only (readable) files
#               in it. No other directories. All files in directory will
#               be read and used for the output.


import sys
import os


def cleanup_list(data_list):
    """Removes newline characters from list items and looks for 
    empty strings in the list and removes them as well
        data_list has to be a list of lists"""
    data = []
    for content in data_list:
        for line in content:
            if "\n" in line:
                no_newline = line.strip("\n")
                data.append(no_newline)
            else:
                data.append(line)

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


def main():
    f_cont_lst = []
    for file in os.listdir(sys.argv[1]):
        with open(os.path.join(sys.argv[1], file), "r") as f:
            files_content = f.readlines()
                # all files in one list, every file in a seperate list
                # every line of every file as item in that list
            f_cont_lst.append(files_content) 

    all_data = cleanup_list(f_cont_lst)

    data_id_dict = ID_data(all_data)
    
    for key in sorted(data_id_dict):
        print(key, ":", data_id_dict[key])


if __name__ == "__main__":
    main()