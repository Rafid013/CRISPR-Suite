import pickle as pkl

import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.feature_selection import SelectFromModel
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC


train_x = pd.read_hdf('features_all.h5')
train_y = pd.read_hdf('labels_all.h5')

extraTree = ExtraTreesClassifier(n_estimators=500, n_jobs=-1, random_state=1)

steps = [('SFM', SelectFromModel(estimator=extraTree)),
         ('scaler', StandardScaler()),
         ('SVM', SVC(C=10, gamma=0.001, kernel='rbf', random_state=1, probability=True,
                     cache_size=20000, verbose=2, shrinking=False))]

pipeline = Pipeline(steps)

pipeline.fit(train_x, train_y)

f = open('cps.pkl', 'wb')
pkl.dump(pipeline, f)
