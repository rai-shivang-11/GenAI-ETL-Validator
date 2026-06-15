# This script generates anomalous data for testing

import numpy as np
import pandas as pd
import os

vDebug = 1

os.makedirs("data", exist_ok = True)

n = 500

df_baseline = pd.DataFrame({
    "id": range(1, n+1),
    "name": [f"user_{i}" for i in range(1, n+1)],
    "age": np.random.randint(18, 100, n),
    "email": [f"user{i}@random.com" for i in range(1, n+1)],
    "amount": np.round(np.random.uniform(100, 500, n), 2),
    "region": np.random.choice(["North", "South", "East", "West"]),
    "date": pd.date_range("2024-01-01", periods= n, freq= "D").astype(str) #Frequency date
})

df_baseline.to_csv("data/baseline.csv", index= False) #No index column added

if vDebug: print("Baseline Created")

# Creating anomalous file

df_current = df_baseline.copy() # if .copy() was not used both these dfs would point to the same object in memory

df_current = df_current.rename(columns= {'date': 'transaction_date'})

df_current['loyalty_score'] = np.random.randint(0, 100, n)

df_current = df_current.drop(columns= ['region'])

vNullIndices = np.random.choice(n, 50, replace = False) # 0 - n, select 40, cannot choose same number twice
vOutlierIndices = np.random.choice(n, 10, replace = False)

df_current.loc[vNullIndices, 'age'] = np.nan #Adding Nulls
df_current.loc[vOutlierIndices, 'amount'] = np.round(np.random.uniform(1000000, 2000000, 10), 2) #Adding exceptionally alrge values

df_current['age'] = df_current['age'].astype(str)

df_current.to_csv('data/current.csv', index= False)

if vDebug: print('Current Created')