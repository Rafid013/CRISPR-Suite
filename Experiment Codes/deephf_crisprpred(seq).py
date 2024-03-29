from thundersvm import SVC
from sklearn.model_selection import train_test_split
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectFromModel
from sklearn.pipeline import Pipeline
from sklearn.ensemble import ExtraTreesClassifier
import pickle as pkl
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, matthews_corrcoef, roc_auc_score


cas9_type = int(input("Cas9 Type?: "))
if cas9_type == 1:
    cas9 = 'wt'
elif cas9_type == 2:
    cas9 = 'esp'
else:
    cas9 = 'sp'

features = pd.DataFrame(pd.read_hdf('../Experiment Data/deephf_x.h5', key='deephf'))
labels = pd.DataFrame(pd.read_hdf('../Experiment Data/deephf_y_' + cas9 + '.h5', key='deephf'))

data = pd.concat([features, labels], axis=1, ignore_index=True)

data = data.dropna().reset_index(drop=True)

train_data, test_data = train_test_split(data, test_size=0.15, random_state=1, stratify=data.iloc[:, -1])

extraTree = ExtraTreesClassifier(n_estimators=500, n_jobs=-1, random_state=1, verbose=2)

steps = [('SFM', SelectFromModel(estimator=extraTree)),
         ('scaler', StandardScaler()),
         ('SVM', SVC(C=10, gamma=0.001, kernel='rbf', cache_size=20000, verbose=True,
                     max_mem_size=6000, probability=True))]

train_x = train_data.iloc[:, :-1]
train_y = train_data.iloc[:, -1]
test_x = test_data.iloc[:, :-1]
test_y = test_data.iloc[:, -1]

if train_y.iloc[0] == 0:
    idx = 1
else:
    idx = 0

model = Pipeline(steps)
model.fit(train_x, train_y)

predict = model.predict(test_x)
predict_proba = model.predict_proba(test_x)[:, idx]

acc = accuracy_score(test_y, predict)
pre = precision_score(test_y, predict)
rec = recall_score(test_y, predict)
f1 = f1_score(test_y, predict)
mcc = matthews_corrcoef(test_y, predict)
roc = roc_auc_score(test_y, predict_proba)

f = open('../Experiment Logs/' + cas9 + '_crisprpred(seq)_log.txt', 'w')
f.write("Accuracy: " + str(acc) + '\n')
f.write("Precision: " + str(pre) + '\n')
f.write("Recall: " + str(rec) + '\n')
f.write("F1 Score: " + str(f1) + '\n')
f.write("Matthews Correlation Coefficient: " + str(mcc) + '\n')
f.write("ROC AUC Score: " + str(roc) + '\n')
f.close()

sfm = model['SFM']
trained_rf = sfm.estimator_
scaler = model['scaler']
svm = model['SVM']

f = open('../Experiment Models/crisprpred(seq)_sfm_' + cas9 + '.pkl', 'wb')
pkl.dump(sfm, f)

f = open('../Experiment Models/crisprpred(seq)_rf_' + cas9 + '.pkl', 'wb')
pkl.dump(trained_rf, f)

f = open('../Experiment Models/crisprpred(seq)_scaler_' + cas9 + '.pkl', 'wb')
pkl.dump(scaler, f)

svm.save_to_file('../Experiment Models/crisprpred(seq)_svm_' + cas9 + '.txt')
