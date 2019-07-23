import matplotlib.pyplot as plt
from sklearn import metrics


def draw_pr_curve(y_true, y_pred):
    plt.figure(figsize=(6, 5))
    plt.title('Precision Recall Curve')

    p, r, threshold = metrics.precision_recall_curve(y_true, y_pred)
    pr_auc = metrics.average_precision_score(y_true, y_pred)
    plt.plot(r, p, label='PR AUC = %0.2f' % pr_auc)
    plt.legend(loc='lower right')

    plt.xlim([0, 1])
    plt.ylim([0, 1])
    plt.ylabel('Precision')
    plt.xlabel('Recall')
    plt.legend(loc='lower left', fancybox=True, shadow=True, ncol=1)
    return plt


def draw_multiple_pr_curve(y_true, y_pred_list, labels):
    plt.figure(figsize=(6, 5))
    plt.title('Precision Recall Curve')

    for y_pred, label in zip(y_pred_list, labels):
        p, r, threshold = metrics.precision_recall_curve(y_true, y_pred)
        pr_auc = metrics.average_precision_score(y_true, y_pred)
        plt.plot(r, p, label=label + ' PR AUC = %0.2f' % pr_auc)
        plt.legend(loc='lower right')

    plt.xlim([0, 1])
    plt.ylim([0, 1])
    plt.ylabel('Precision')
    plt.xlabel('Recall')
    plt.legend(loc='lower left', fancybox=True, shadow=True, ncol=1)
    return plt
