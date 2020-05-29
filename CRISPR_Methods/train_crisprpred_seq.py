import pickle as pkl
import smtplib
import ssl
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.feature_selection import SelectFromModel
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from generate_features import position_independent, position_specific, gap_features
from django.core.mail import send_mail


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
pos_ind = position_independent(training_file, 4).astype(np.int8)
pos_spe = position_specific(training_file, 4).astype(np.int8)
gap = gap_features(training_file).astype(np.int8)
train_x = pd.concat([pos_ind, pos_spe, gap], axis=1, sort=False)

extraTree = ExtraTreesClassifier(n_estimators=500, n_jobs=-1, random_state=1)

steps = [('SFM', SelectFromModel(estimator=extraTree)),
         ('scaler', StandardScaler()),
         ('SVM', SVC(C=10, gamma=0.001, kernel='rbf', random_state=1, probability=True,
                     cache_size=20000, verbose=2, shrinking=False))]

pipeline = Pipeline(steps)

pipeline.fit(train_x, train_y)

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

The training of the model " + model_name + " has finished."""

with smtplib.SMTP(smtp_server, port) as server:
    server.ehlo()
    server.starttls(context=context)
    server.ehlo()
    server.login(sender_email, password)
    server.sendmail(sender_email, receiver_email, message)
