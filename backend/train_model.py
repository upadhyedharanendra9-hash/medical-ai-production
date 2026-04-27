import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

# Training on Generic Feature Slots
# Slot 1 & 2: Continuous Numbers | Slot 3 & 4: Binary Categories
data = {
    'feat1': [10, 50, 20, 15, 45, 12, 35, 25],
    'feat2': [100, 200, 150, 110, 190, 105, 170, 130],
    'feat3': [1, 0, 1, 0, 1, 0, 1, 0], 
    'feat4': [0, 1, 0, 0, 1, 0, 1, 0],
    'target': [0, 1, 0, 0, 1, 0, 1, 0] # Generic outcome (Risk, Default, Churn, etc.)
}

df = pd.DataFrame(data)
X = df[['feat1', 'feat2', 'feat3', 'feat4']]
y = df['target']

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

joblib.dump(model, "universal_model.pkl")
print("✅ Universal Brain Created: universal_model.pkl")