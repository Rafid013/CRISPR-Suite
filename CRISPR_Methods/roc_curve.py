import matplotlib.pyplot as plt
from sklearn import metrics


def draw_roc_curve(y_true, y_score):
    plt.figure(figsize=(6, 5))
    plt.title('Receiver Operating Characteristic Curve')

    fpr, tpr, threshold = metrics.roc_curve(y_true, y_score)
    roc_auc = metrics.auc(fpr, tpr)
    plt.plot(fpr, tpr, label='ROC AUC = %0.2f' % roc_auc)
    plt.legend(loc='lower right')

    plt.plot([0, 1], [0, 1], '--')
    plt.xlim([0, 1])
    plt.ylim([0, 1])
    plt.ylabel('True Positive Rate')
    plt.xlabel('False Positive Rate')
    plt.legend(loc='lower right', fancybox=True, shadow=True, ncol=1)
    return plt


def draw_multiple_roc_curve(y_true, y_score_list, labels):
    plt.figure(figsize=(6, 5))
    plt.title('Receiver Operating Characteristic Curve')

    for y_score, label in zip(y_score_list, labels):
        fpr, tpr, threshold = metrics.roc_curve(y_true, y_score)
        roc_auc = metrics.auc(fpr, tpr)
        plt.plot(fpr, tpr, label=label + ' AUC = %0.2f' % roc_auc)
        plt.legend(loc='lower right')

    plt.plot([0, 1], [0, 1], '--')
    plt.xlim([0, 1])
    plt.ylim([0, 1])
    plt.ylabel('True Positive Rate')
    plt.xlabel('False Positive Rate')
    plt.legend(loc='lower right', fancybox=True, shadow=True, ncol=1)
    return plt
