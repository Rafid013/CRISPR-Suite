import pandas as pd
import numpy as np

data = pd.read_excel('../Experiment Data/deephf_data.xlsx', skiprows=1)
wt_efficiency = []
espcas9_efficiency = []
spcas9_hf1_efficiency = []
for idx, row in data.iterrows():
    if row['Wt_Efficiency'] >= 0.5:
        wt_efficiency.append(1)
    elif row['Wt_Efficiency'] < 0.5:
        wt_efficiency.append(0)
    else:
        wt_efficiency.append(np.nan)

    if row['eSpCas 9_Efficiency'] >= 0.5:
        espcas9_efficiency.append(1)
    elif row['eSpCas 9_Efficiency'] < 0.5:
        espcas9_efficiency.append(0)
    else:
        espcas9_efficiency.append(np.nan)

    if row['SpCas9-HF1_Efficiency'] >= 0.5:
        spcas9_hf1_efficiency.append(1)
    elif row['SpCas9-HF1_Efficiency'] < 0.5:
        spcas9_hf1_efficiency.append(0)
    else:
        spcas9_hf1_efficiency.append(np.nan)


data['Wt_Efficiency_Class'] = pd.Series(wt_efficiency)
data['eSpCas 9_Efficiency_Class'] = pd.Series(espcas9_efficiency)
data['SpCas9-HF1_Efficiency_Class'] = pd.Series(spcas9_hf1_efficiency)
data.to_csv('../Experiment Data/deephf_data.csv', sep=',', index=False)
