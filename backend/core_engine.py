import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_recall_curve
import joblib

class MedicalAICore:
    def __init__(self):
        self.pipeline = None
        self.best_threshold = 0.5

    def build_pipeline(self, X):
        numeric_features = ['age', 'blood_pressure']
        categorical_features = ['gender', 'smoker']

        numeric_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler())
        ])

        categorical_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
            ('onehot', OneHotEncoder(handle_unknown='ignore'))
        ])

        preprocessor = ColumnTransformer(transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)
        ])

        self.pipeline = Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
        ])

    def train_and_tune(self, X, y):
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        self.build_pipeline(X_train)
        self.pipeline.fit(X_train, y_train)

        # Tune for 90% Recall to ensure medical safety
        y_scores = self.pipeline.predict_proba(X_test)[:, 1]
        precisions, recalls, thresholds = precision_recall_curve(y_test, y_scores)
        idx = np.where(recalls >= 0.90)[0][-1]
        self.best_threshold = float(thresholds[idx])

    def save(self, path):
        joblib.dump({"pipeline": self.pipeline, "threshold": self.best_threshold}, path)