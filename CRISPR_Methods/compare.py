import pickle as pkl
import sys
from generate_features import position_independent, position_specific, gap_features
import pandas as pd
import numpy as np
import os
import smtplib
import ssl
from sklearn.metrics import accuracy_score, roc_auc_score, precision_score, recall_score, f1_score, matthews_corrcoef
from pr_curve import draw_multiple_pr_curve
from roc_curve import draw_multiple_roc_curve
from metrics_table import plot_metrics_table
from django.core.mail import send_mail

# get user_id, model_ids, model_types, model_names, prediction_file, email in command line input
user_id = sys.argv[1]
model_ids = sys.argv[2]
model_types = sys.argv[3]
model_names = sys.argv[4]
prediction_file = sys.argv[5]
email = sys.argv[6]

model_directory = 'saved_models/'
media_directory = 'media/'
prediction_directory = 'predictions/'
static_directory = 'static/'

test_file = pd.read_csv(media_directory + prediction_file, delimiter=',')

test_file_x = test_file['sgRNA']
test_file_y = test_file['label']

pos_ind = position_independent(test_file, 4).astype(np.int8)
pos_spe = position_specific(test_file, 4).astype(np.int8)
gap = gap_features(test_file)

model_id_list = str(model_ids).split(sep='_')
model_type_list = str(model_types).split(sep='_')
model_name_list = str(model_names).split(sep='_')

predictions = []
prediction_probas = []

for model_id, model_type in zip(model_id_list, model_type_list):
    f = open(model_directory + model_id + '.pkl', 'rb')
    model = pkl.load(f)

    if model_type == '1':
        test_x = pd.concat([pos_ind, pos_spe], axis=1, sort=False)
    else:
        test_x = pd.concat([pos_ind, pos_spe, gap], axis=1, sort=False)

    prediction_y = model.predict(test_x)
    prediction_y_proba = model.predict_proba(test_x)[:, 1]

    predictions.append(prediction_y)
    prediction_probas.append(prediction_y_proba)

os.remove(media_directory + prediction_file)

if not os.path.exists(static_directory + 'user_' + str(user_id)):
    os.makedirs(static_directory + 'user_' + str(user_id))

metrics = pd.DataFrame()
metrics['Metrics'] = pd.Series(['Accuracy', 'ROC AUC', 'Precision', 'Recall', 'F1 Score', 'MCC'])
for prediction, prediction_proba, model_name in zip(predictions, prediction_probas, model_name_list):
    acc = accuracy_score(test_file_y, prediction)
    roc = roc_auc_score(test_file_y, prediction_proba)
    pre = precision_score(test_file_y, prediction)
    rec = recall_score(test_file_y, prediction)
    f1 = f1_score(test_file_y, prediction)
    mcc = matthews_corrcoef(test_file_y, prediction)

    metrics[model_name] = pd.Series([acc, roc, pre, rec, f1, mcc])

metrics_table_plt = plot_metrics_table(metrics)
metrics_table_plt.savefig(static_directory + 'user_' + str(user_id) + '/comparison_metrics.png')

pr_curve_plt = draw_multiple_pr_curve(test_file_y, predictions, model_name_list)
pr_curve_plt.savefig(static_directory + 'user_' + str(user_id) + '/comparison_pr_curve.png')

roc_curve_plt = draw_multiple_roc_curve(test_file_y, prediction_probas, model_name_list)
roc_curve_plt.savefig(static_directory + 'user_' + str(user_id) + '/comparison_roc_curve.png')

port = 465  # For SSL
password = "crisprsuite123"

# Create a secure SSL context
context = ssl.create_default_context()

sender_email = "crisprsuite@gmail.com"
receiver_email = email
message = "" \
          "The comparison metrics are now available."
subject = "Comparison Completed"
send_mail(subject, message, sender_email, [receiver_email], fail_silently=False)

# with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
#     server.login(sender_email, password)
#     server.sendmail(sender_email, receiver_email, message)
