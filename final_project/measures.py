from collections import Counter
from nltk.metrics import ConfusionMatrix
import sys
import formatting as form
import os


def measures(ref, tagged):
    """Measures as given to calculate the f-score, recall end precision, as
    well as printing a confusionmatrix."""
    cm = ConfusionMatrix(ref, tagged)

    print(cm)

    labels = set(ref + tagged)

    true_positives = Counter()
    false_negatives = Counter()
    false_positives = Counter()

    for i in labels:
        for j in labels:
            if i == j:
                true_positives[i] += cm[i, j]
            else:
                false_negatives[i] += cm[i, j]
                false_positives[j] += cm[i, j]

    print("TP:", sum(true_positives.values()), true_positives)
    print("FN:", sum(false_negatives.values()), false_negatives)
    print("FP:", sum(false_positives.values()), false_positives)
    print()

    for i in sorted(labels):
        print(f"{i}:")
        if true_positives[i] == 0:
            fscore = 0
            print(f"\tfscore:\t\t {fscore}")
        else:
            precision = true_positives[i] / float(true_positives[i] +
                                                  false_positives[i])
            recall = true_positives[i] / float(true_positives[i] +
                                               false_negatives[i])
            fscore = 2 * (precision * recall) / float(precision + recall)

            print(f"\tfscore:\t\t {fscore}")
            print(f"\trecall:\t\t {recall}")
            print(f"\tprecision:\t {precision}")
        



def main():
    filenames = os.listdir(sys.argv[1])
    dir_sorted = sorted(filenames)

    system_dict = {}
    test_dict = {}

    for dir in dir_sorted: #dir_sorted
        with open(os.path.join(sys.argv[1], dir, "system.en.tok.off.pos.ent"), "r") as f:
            system_file_content = f.readlines()
        with open(os.path.join(sys.argv[1], dir, "en.tok.off.pos.ent"), "r") as fl:
            test_file_content = fl.readlines()
        
        system_lines = [line.rstrip() for line in system_file_content]
        test_lines = [line.rstrip() for line in test_file_content]


        system_dict[dir] = system_lines
        test_dict[dir] = test_lines
        
    
    
    annA_content = system_dict
    annB_content = test_dict

    overlap_data = form.find_annotations(filenames, annA_content, annB_content)

    print("precision, recall, and f-score for interesting entities vs non-interesting entities:")
    print()
    print()
    annotatedA = overlap_data["column_six_A"]
    annotatedB = overlap_data["column_six_B"]
    measures(annotatedA, annotatedB)

    print()
    print("____________________________________________________________________________________")
    print()
    print()

    print("precision, recall, and f-score for all entities:")
    print()
    print()
    annA = overlap_data["data_A"]
    annB = overlap_data["data_B"]
    measures(annA, annB)


if __name__ == "__main__":
    main()