import pandas as pd
import numpy as np
import xgboost as xgb
import glob
from pathlib import Path
import joblib

def train_and_save_model():
    print("Loading labeled data...")
    path = Path("data/ovrednoteni_podatki")
    all_files = glob.glob(str(path / "m*.csv"))
    
    li = []
    for filename in all_files:
        df_temp = pd.read_csv(filename, sep=",", decimal=".", header=None, encoding="cp1250")
        li.append(df_temp)
        
    df_oznaceno = pd.concat(li, axis=0, ignore_index=True)
    df_oznaceno.columns = ["ID Merilnika", "Čas", "meritev", "anomalija"]
    
    # Feature Engineering
    print("Engineering features...")
    df_oznaceno = df_oznaceno.sort_values(['ID Merilnika', 'Čas'])
    
    for i in range(1, 4):
        df_oznaceno[f'lag_{i}'] = df_oznaceno.groupby('ID Merilnika')['meritev'].shift(i)
        
    df_oznaceno['rolling_mean'] = df_oznaceno.groupby('ID Merilnika')['meritev'].transform(lambda x: x.rolling(window=5).mean())
    df_oznaceno['rolling_std'] = df_oznaceno.groupby('ID Merilnika')['meritev'].transform(lambda x: x.rolling(window=5).std())
    df_oznaceno['velocity'] = df_oznaceno.groupby('ID Merilnika')['meritev'].diff()
    
    df_clean = df_oznaceno.dropna().copy()
    df_clean = df_clean.sort_values('Čas')
    
    features = ['meritev', 'lag_1', 'lag_2', 'lag_3', 'rolling_mean', 'rolling_std', 'velocity']
    X = df_clean[features]
    y = df_clean['anomalija']
    
    print("Training XGBClassifier...")
    model = xgb.XGBClassifier(random_state=42)
    model.fit(X, y)
    
    model_path = path.parent.parent / "xgboost_anomaly_model.pkl"
    joblib.dump(model, model_path)
    print(f"Model saved via joblib to {model_path}")

if __name__ == '__main__':
    train_and_save_model()
