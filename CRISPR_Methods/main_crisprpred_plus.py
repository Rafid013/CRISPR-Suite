import pickle as pkl

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectFromModel
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC


train_x = pd.read_hdf('features_all.h5')
train_y = pd.read_hdf('labels_all.h5')

rf = RandomForestClassifier(n_estimators=500, n_jobs=-1, random_state=1, verbose=2)

steps = [('SFM', SelectFromModel(estimator=rf, max_features=3500, threshold=-np.inf)),
         ('scaler', StandardScaler()),
         ('SVM', SVC(C=1, gamma='auto', kernel='rbf',
                     random_state=1, probability=True, cache_size=20000, verbose=2))]

pipeline = Pipeline(steps)

pipeline.fit(train_x, train_y)

f = open('cpp.pkl', 'wb')
pkl.dump(pipeline, f)
