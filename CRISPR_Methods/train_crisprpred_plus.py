import pickle as pkl
import smtplib
import ssl
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectFromModel
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
import os
from generate_features import position_independent, position_specific, gap_features


# get project_id, project_name, model_name, filename, email in command line input
project_id = sys.argv[1]
project_name = sys.argv[2]
model_name = sys.argv[3]
filename = sys.argv[4]
email = sys.argv[5]

print(email)

media_directory = 'media/'
model_directory = 'saved_models/'

training_file = pd.read_csv(media_directory + filename, delimiter=',')
train_y = pd.DataFrame(training_file['label'].astype(np.int8), columns=['label'])
pos_ind = position_independent(training_file, 4).astype(np.int8)
pos_spe = position_specific(training_file, 4).astype(np.int8)
gap = gap_features(training_file).astype(np.int8)
train_x = pd.concat([pos_ind, pos_spe, gap], axis=1, sort=False)

rf = RandomForestClassifier(n_estimators=500, n_jobs=-1, random_state=1)

steps = [('SFM', SelectFromModel(estimator=rf, max_features=3500, threshold=-np.inf)),
         ('scaler', StandardScaler()),
         ('SVM', SVC(C=1, gamma='auto', kernel='rbf', random_state=1, probability=True,
                     cache_size=20000, verbose=2, shrinking=False))]

pipeline = Pipeline(steps)

pipeline.fit(train_x, train_y)

if not os.path.exists(model_directory + 'project_' + str(project_id)):
    os.makedirs(model_directory + 'project_' + str(project_id))

f = open(model_directory + 'project_' + str(project_id) + '/' + model_name + '.pkl', 'wb')
pkl.dump(pipeline, f)

port = 465  # For SSL
password = "crisprsuite123"

# Create a secure SSL context
context = ssl.create_default_context()

sender_email = "crisprsuite@gmail.com"
receiver_email = email
message = "Subject: Training Finished\n\nThe training of the model " + model_name + " in project " +\
          project_name + " has finished training."

with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
    server.login(sender_email, password)
    server.sendmail(sender_email, receiver_email, message)
