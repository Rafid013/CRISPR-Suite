import pickle as pkl
import sys
from generate_features import position_independent, position_specific, gap_features
import pandas as pd
import numpy as np
import os
import smtplib
import ssl


# get project_id, project_name, model_type, model_name, prediction_file, email in command line input
project_id = sys.argv[1]
project_name = sys.argv[2]
model_type = sys.argv[3]
model_name = sys.argv[4]
prediction_file = sys.argv[5]
email = sys.argv[6]

project_directory = 'media/'

f = open(project_directory + 'project_' + str(project_id) + '/' + model_name + '.pkl', 'rb')
model = pkl.load(f)


test_file = pd.read_csv(project_directory + prediction_file, delimiter=',')
pos_ind = position_independent(test_file, 4).astype(np.int8)
pos_spe = position_specific(test_file, 4).astype(np.int8)
if str(model_type) == '1':
    test_x = pd.concat([pos_ind, pos_spe], axis=1, sort=False)
else:
    gap = gap_features(test_file)
    test_x = pd.concat([pos_ind, pos_spe, gap], axis=1, sort=False)

prediction_y = model.predict(test_x)

to_save = pd.DataFrame()
to_save['sgRNA'] = test_file['sgRNA']
to_save['label'] = pd.Series(prediction_y)
to_save.to_csv(project_directory + 'project_' + str(project_id) + '/' + model_name + '_prediction.csv', sep=',',
               index=False)

os.remove(project_directory + prediction_file)

port = 465  # For SSL
password = "crisprsuite123"

# Create a secure SSL context
context = ssl.create_default_context()

sender_email = "crisprsuite@gmail.com"
receiver_email = email
message = "Subject: Prediction Finished\n\nThe prediction of the model " + model_name + " in project " +\
          project_name + " is available."

with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
    server.login(sender_email, password)
    server.sendmail(sender_email, receiver_email, message)
