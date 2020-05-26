import pickle as pkl
import smtplib
import ssl
import sys

from django.conf import settings

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectFromModel
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from generate_features import position_independent, position_specific, gap_features
from django.core.mail import send_mail



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
train_x = pd.concat([pos_ind, pos_spe], axis=1, sort=False)

rf = RandomForestClassifier(n_estimators=500, n_jobs=-1, random_state=1, verbose=2)

steps = [('SFM', SelectFromModel(estimator=rf, max_features=2899, threshold=-np.inf)),
         ('scaler', StandardScaler()),
         ('SVM', SVC(C=1, gamma='auto', kernel='rbf',
                     random_state=1, probability=True, cache_size=20000, verbose=2))]

pipeline = Pipeline(steps)

pipeline.fit(train_x, train_y)

f = open(model_directory + model_id + '.pkl', 'wb')
pkl.dump(pipeline, f)

port = settings.EMAIL_PORT
password = settings.EMAIL_HOST_PASSWORD

# Create a secure SSL context
context = ssl.create_default_context()

sender_email = settings.EMAIL_USER_NAME
receiver_email = email
message = "The training of the model " + model_name + " has finished."
subject = "Training Completed"
send_mail(subject, message, sender_email, [receiver_email], fail_silently=False)

# with smtplib.SMTP(settings.EMAIL_HOST_USER, port) as server:
#     server.starttls(context=context)
#     server.login(sender_email, password)
#     server.sendmail(sender_email, receiver_email, message)
