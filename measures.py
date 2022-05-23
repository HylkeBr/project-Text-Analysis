from collections import Counter
from nltk.metrics import ConfusionMatrix
import sys
import formatting as form


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
        if true_positives[i] == 0:
            fscore = 0
        else:
            precision = true_positives[i] / float(true_positives[i] +
                                                  false_positives[i])
            recall = true_positives[i] / float(true_positives[i] +
                                               false_negatives[i])
            fscore = 2 * (precision * recall) / float(precision + recall)
        print(f"{i}:")
        print(f"\tfscore:\t\t {fscore}")
        print(f"\trecall:\t\t {recall}")
        print(f"\tprecision:\t {precision}")


def main():
    filenames = ["d0071", "d0076", "d0112", "d0117", "d0195", "d0271", "d0315", "d0337",
    "d0527", "d0577", "d0583", "d0592", "d0616", "d0622", "d0653", "d0675", "d0688", "d0691"]
    
    annA_content = form.mk_dict(filenames, sys.argv[1])
    annB_content = form.mk_dict(filenames, sys.argv[2])

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