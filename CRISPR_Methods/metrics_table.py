import matplotlib.pyplot as plt


def plot_metrics_table(dataframe):
    plt.table(cellText=dataframe.values, colWidths=[0.25] * len(dataframe.columns),
              rowLabels=None,
              colLabels=dataframe.columns,
              cellLoc='center', rowLoc='center',
              loc='center')
    plt.axis('off')
    return plt
