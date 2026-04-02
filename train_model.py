import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import pickle

# 1. Create a "Smart" Dataset
np.random.seed(42)
n_samples = 2000

# Features: [Type, AirTemp, ProcTemp, Speed, Torque, Wear]
data = {
    'Type': np.random.choice([0, 1, 2], n_samples),
    'AirTemp': np.random.uniform(285, 310, n_samples),
    'ProcTemp': np.random.uniform(290, 350, n_samples),
    'Speed': np.random.uniform(500, 4500, n_samples),
    'Torque': np.random.uniform(10, 95, n_samples),
    'Wear': np.random.uniform(0, 250, n_samples)
}

df = pd.DataFrame(data)

# 2. Logic: Define what "Failure" looks like
# If ProcTemp > 330 AND Wear > 180, it's almost certainly a failure (1)
score = (
    (df['ProcTemp'] - 290) * 0.4 + 
    (df['Wear'] * 0.3) + 
    (df['Torque'] * 0.2) +
    (df['Type'] * 5)
)
# Normalize and create Target (0 = Healthy, 1 = Fail)
df['Target'] = (score > np.percentile(score, 75)).astype(int)

# 3. Train the Model
X = df.drop('Target', axis=1)
y = df['Target']

model = RandomForestClassifier(n_estimators=100)
model.fit(X, y)

# 4. Save with Metadata
with open("model.pkl", "wb") as f:
    pickle.dump({"model": model, "features": list(X.columns)}, f)

print("✅ Success! New model.pkl generated with varied logic.")