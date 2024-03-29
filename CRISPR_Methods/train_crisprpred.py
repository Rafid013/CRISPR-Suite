import pickle as pkl
import ssl
import sys
import smtplib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectFromModel
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from generate_features import position_independent, position_specific, gap_features
import time


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'crispr@grad.cse.buet.ac.bd'
EMAIL_USER_NAME = 'crispr@grad.cse.buet.ac.bd'
EMAIL_HOST_PASSWORD = 'genomePrediction2020'
EMAIL_PORT = 587

# get model_id, model_name, filename, email in command line input
model_id = sys.argv[1]
model_name = sys.argv[2]
filename = sys.argv[3]
email = sys.argv[4]

media_directory = 'media/'
model_directory = 'saved_models/'

training_file = pd.read_csv(media_directory + filename, delimiter=',')
train_y = pd.DataFrame(training_file['label'].astype(np.int8), columns=['label'])

feature_start_time = time.time()
pos_ind = position_independent(training_file, 4).astype(np.int8)
pos_spe = position_specific(training_file, 4).astype(np.int8)
feature_end_time = time.time()
print('Feature generation time: ' + str(feature_end_time - feature_start_time))

train_x = pd.concat([pos_ind, pos_spe], axis=1, sort=False)

rf = RandomForestClassifier(n_estimators=500, n_jobs=-1, random_state=1, verbose=2)

steps = [('SFM', SelectFromModel(estimator=rf, max_features=2899, threshold=-np.inf)),
         ('scaler', StandardScaler()),
         ('SVM', SVC(C=1, gamma='auto', kernel='rbf',
                     random_state=1, probability=True, cache_size=20000, verbose=2))]

pipeline = Pipeline(steps)

training_start_time = time.time()
pipeline.fit(train_x, train_y)
training_end_time = time.time()
print('Training time: ' + str(training_end_time - training_start_time))

f = open(model_directory + model_id + '.pkl', 'wb')
pkl.dump(pipeline, f)

port = EMAIL_PORT
password = EMAIL_HOST_PASSWORD
smtp_server = EMAIL_HOST

# Create a secure SSL context
context = ssl.SSLContext(ssl.PROTOCOL_TLS)

sender_email = EMAIL_USER_NAME
receiver_email = email
message = """\
Subject: Training Completed

The training of the model """ + model_name + """ has finished."""

with smtplib.SMTP(smtp_server, port) as server:
    server.ehlo()
    server.starttls(context=context)
    server.ehlo()
    server.login(sender_email, password)
    server.sendmail(sender_email, receiver_email, message)
