from sklearn.model_selection import train_test_split
import pandas as pd


data = pd.read_csv('../Experiment Data/deephf_data.csv', delimiter=',')
data.interpolate(method='linear', limit_direction='both', inplace=True)

train_wt_data, test_wt_data = train_test_split(data, test_size=0.15, stratify=data['Wt_Efficiency_Class'])

train_esp_data, test_esp_data = train_test_split(data, test_size=0.15, stratify=data['eSpCas 9_Efficiency_Class'])

train_sp_data, test_sp_data = train_test_split(data, test_size=0.15, stratify=data['SpCas9-HF1_Efficiency_Class'])

train_wt_data.to_csv('../Experiment Data/Train_WT.csv', sep=',', index=False)
test_wt_data.to_csv('../Experiment Data/Test_WT.csv', sep=',', index=False)
train_esp_data.to_csv('../Experiment Data/Train_ESP.csv', sep=',', index=False)
test_esp_data.to_csv('../Experiment Data/Test_ESP.csv', sep=',', index=False)
train_sp_data.to_csv('../Experiment Data/Train_SP.csv', sep=',', index=False)
test_sp_data.to_csv('../Experiment Data/Test_SP.csv', sep=',', index=False)
