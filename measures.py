import sys
import os
import format_files as format


def main():
    content_lst_A = []
    for file_A in os.listdir(sys.argv[1]):
        with open(os.path.join(sys.argv[1], file_A), "r") as f_A:
            files_content_A = f_A.readlines()
            content_lst_A.append(files_content_A) 
    
#    content_lst_B = []
#    for file_B in os.listdir(sys.argv[2]):
#        with open(os.path.join(sys.argv[2], file_B), "r") as f_B:
#            files_content_B = f_B.readlines()
#            content_lst_B.append(files_content_B) 

    ID_data_A = format.ID_data(format.cleanup_list(content_lst_A))
#    ID_data_B = format.ID_data(format.cleanup_list(content_lst_B))

    for key in sorted(ID_data_A):
        print(key, ":", ID_data_A[key])


if __name__ == "__main__":
    main()