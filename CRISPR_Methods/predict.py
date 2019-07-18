import pickle as pkl
import sys
from generate_features import position_independent, position_specific, gap_features
import pandas as pd
import numpy as np
import os
import smtplib
import ssl
from sklearn.metrics import accuracy_score, roc_auc_score, precision_score, recall_score, f1_score, matthews_corrcoef
from pr_curve import draw_pr_curve
from roc_curve import draw_roc_curve
from metrics_table import plot_metrics_table


# get project_id, project_name, model_id, model_type, model_name, prediction_file, email in command line input
project_id = sys.argv[1]
project_name = sys.argv[2]
model_id = sys.argv[3]
model_type = sys.argv[4]
model_name = sys.argv[5]
prediction_file = sys.argv[6]
email = sys.argv[7]

model_directory = 'saved_models/'
media_directory = 'media/'
prediction_directory = 'predictions/'
static_directory = 'static/'

print("predicting....")

if model_id == 'cp':
    f = open(model_directory + 'crisprpred.pkl', 'rb')
    model_name = 'crisprpred'
elif model_id == 'cpp':
    f = open(model_directory + 'crisprpred_plus.pkl', 'rb')
    model_name = 'crisprpred_plus'
elif model_id == 'cps':
    f = open(model_directory + 'crisprpred_seq.pkl', 'rb')
    model_name = 'crisprpred_seq'
else:
    f = open(model_directory + 'project_' + str(project_id) + '/' + model_name + '.pkl', 'rb')
model = pkl.load(f)

test_file = pd.read_csv(media_directory + prediction_file, delimiter=',')

test_file_x = test_file['sgRNA']
test_file_y = pd.DataFrame(data=[])
if test_file.shape[1] == 2:
    test_file_y = test_file['label']

pos_ind = position_independent(test_file, 4).astype(np.int8)
pos_spe = position_specific(test_file, 4).astype(np.int8)
if str(model_type) == '1':
    test_x = pd.concat([pos_ind, pos_spe], axis=1, sort=False)
else:
    gap = gap_features(test_file)
    test_x = pd.concat([pos_ind, pos_spe, gap], axis=1, sort=False)

prediction_y = model.predict(test_x)
prediction_y_proba = model.predict_proba(test_x)

to_save = pd.DataFrame()
to_save['sgRNA'] = test_file_x
if test_file.shape[1] == 2:
    to_save['true label'] = pd.Series(test_file_y)
to_save['predicted label'] = pd.Series(prediction_y)
to_save['prediction probability'] = pd.Series(prediction_y_proba[:, 1])

if not os.path.exists(prediction_directory + 'project_' + str(project_id)):
    os.makedirs(prediction_directory + 'project_' + str(project_id))

to_save.to_csv(prediction_directory + 'project_' + str(project_id) + '/' + model_name + '_prediction.csv', sep=',',
               index=False)

os.remove(media_directory + prediction_file)

if not test_file_y.empty:
    acc = accuracy_score(test_file_y, prediction_y)
    roc = roc_auc_score(test_file_y, prediction_y_proba[:, 1])
    pre = precision_score(test_file_y, prediction_y)
    rec = recall_score(test_file_y, prediction_y)
    f1 = f1_score(test_file_y, prediction_y)
    mcc = matthews_corrcoef(test_file_y, prediction_y)

    if not os.path.exists(static_directory + 'project_' + str(project_id)):
        os.makedirs(static_directory + 'project_' + str(project_id))

    metrics = pd.DataFrame()
    metrics['Metrics'] = pd.Series(['Accuracy', 'ROC AUC', 'Precision', 'Recall', 'F1 Score', 'MCC'])
    metrics['Values'] = pd.Series([acc, roc, pre, rec, f1, mcc])
    metrics_table_plt = plot_metrics_table(metrics)
    metrics_table_plt.savefig(static_directory + 'project_' + str(project_id) + '/' + model_name + '_metrics.png')

    pr_curve_plt = draw_pr_curve(test_file_y, prediction_y)
    pr_curve_plt.savefig(static_directory + 'project_' + str(project_id) + '/' + model_name + '_pr_curve.png')

    roc_curve_plt = draw_roc_curve(test_file_y, prediction_y_proba[:, 1])
    roc_curve_plt.savefig(static_directory + 'project_' + str(project_id) + '/' + model_name + '_roc_curve.png')

port = 465  # For SSL
password = "crisprsuite123"

# Create a secure SSL context
context = ssl.create_default_context()

sender_email = "crisprsuite@gmail.com"
receiver_email = email
message = "Subject: Prediction Finished\n\nThe prediction of the model " + model_name + " in project " + \
          project_name + " is available."

with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
    server.login(sender_email, password)
    server.sendmail(sender_email, receiver_email, message)
