import io
import base64
import traceback
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import logging
import gc
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, r2_score

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nexus_kernel")

plt.switch_backend('Agg')

app = FastAPI(title="Nexus Universal Kernel")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def clean_json(obj):
    if isinstance(obj, dict):
        return {k: clean_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_json(i) for i in obj]
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return 0.0 if np.isnan(obj) or np.isinf(obj) else float(obj)
    elif pd.isna(obj):
        return None
    return obj

def get_b64():
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=120)
    plt.close()
    return base64.b64encode(buf.getvalue()).decode('utf-8')

@app.post("/analyze")
async def universal_master_pipeline(file: UploadFile = File(...)):
    plt.close('all')
    gc.collect()
    steps = []
    try:
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content), sep=None, engine='python', on_bad_lines='skip')

        def record(sid: int, title: str, cmd: str, out=None, img=None):
            steps.append({
                "id": sid,
                "title": title,
                "cmd": cmd,
                "out": out,
                "img": img,
                "pct": int((sid / 17) * 100)
            })

        record(1, "Kernel Boot", "sys.init()", "Universal Logic Locked.")
        record(2, "Data Ingestion", "pd.read_csv()", df.head(5).to_html(classes='p-table'))
        record(3, "Schema Discovery", "df.info()", f"{df.shape[0]:,} rows × {df.shape[1]} columns")
        record(4, "Integrity Audit", "df.isnull().sum()", df.isnull().sum().to_frame(name='Missing').to_html(classes='p-table'))

        target_candidates = ['target', 'label', 'class', 'status', 'outcome', 'y', 'churn', 'cancel', 'fraud', 'survived', 'cardio']
        target = next((c for c in df.columns if any(k in c.lower() for k in target_candidates)), df.columns[-1])

        y_series = df[target]
        n_unique = y_series.nunique()

        if n_unique <= 10 and pd.api.types.is_numeric_dtype(y_series):
            y_series = y_series.round().astype(int)

        is_classification = n_unique <= 10

        record(5, "Target Identification", f"Target = '{target}'", 
               f"Type: {'Classification' if is_classification else 'Regression'} | Unique: {n_unique}")

        plt.figure(figsize=(10, 5))
        if is_classification:
            sns.countplot(y=y_series.astype(str), hue=y_series.astype(str), palette='Blues', legend=False)
        else:
            sns.histplot(df[target], kde=True, color='#3b82f6')
        record(6, "Target Distribution", f"Distribution of {target}", img=get_b64())

        record(7, "Descriptive Stats", "df.describe()", df.describe(include='all').round(3).to_html(classes='p-table'))

        plt.figure(figsize=(11, 7))
        numeric_df = df.select_dtypes(include=[np.number])
        if not numeric_df.empty:
            sns.heatmap(numeric_df.corr(), cmap='Blues', annot=False)
        record(8, "Correlation Matrix", "sns.heatmap()", img=get_b64())

        proc_df = df.copy()
        num_cols = proc_df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = proc_df.select_dtypes(exclude=[np.number]).columns.tolist()

        proc_df[num_cols] = proc_df[num_cols].fillna(proc_df[num_cols].median())
        proc_df[cat_cols] = proc_df[cat_cols].fillna("Missing")
        record(9, "Imputation", "fillna(median/mode)", "Missing values handled.")

        for col in cat_cols:
            le = LabelEncoder()
            proc_df[col] = le.fit_transform(proc_df[col].astype(str))
        record(10, "Label Encoding", "LabelEncoder()", f"{len(cat_cols)} columns encoded.")

        if num_cols:
            scaler = StandardScaler()
            proc_df[num_cols] = scaler.fit_transform(proc_df[num_cols])
        record(11, "Feature Scaling", "StandardScaler()", "Numeric features normalized.")

        if num_cols:
            plt.figure(figsize=(12, 5))
            proc_df[num_cols[:min(5, len(num_cols))]].boxplot()
            record(12, "Outlier Analysis", "Boxplot", img=get_b64())

        X = proc_df.drop(columns=[target])
        y = y_series if is_classification else proc_df[target]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
        record(13, "Data Partitioning", "train_test_split(0.25)", f"Train: {len(X_train)} | Test: {len(X_test)}")

        if is_classification:
            model = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
            preds = model.fit(X_train, y_train).predict(X_test)
            score = accuracy_score(y_test, preds)
            metric = "Accuracy"
        else:
            model = RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1)
            preds = model.fit(X_train, y_train).predict(X_test)
            score = r2_score(y_test, preds)
            metric = "R² Score"

        record(14, "Model Training", f"RandomForest({'Classifier' if is_classification else 'Regressor'})", f"{metric}: {score:.4f}")

        plt.figure(figsize=(10, 6))
        plt.scatter(y_test, preds, alpha=0.6, color='#3b82f6')
        plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--')
        record(15, "Validation Plot", "Actual vs Predicted", img=get_b64())

        record(16, "Benchmarking", "Evaluation", f"Final {metric}: {score:.4f}")

        imp = sorted([{"name": col, "val": float(val)} for col, val in zip(X.columns, model.feature_importances_)], 
                     key=lambda x: x['val'], reverse=True)[:10]

        plt.figure(figsize=(11, 6))
        sns.barplot(x=[x['val'] for x in imp], y=[x['name'] for x in imp], 
                    hue=[x['name'] for x in imp], palette='Blues_r', legend=False)
        record(17, "Feature Importance", "Top 10 Drivers", img=get_b64())

        record(17, "Cleaned Dataset Export", "proc_df.to_csv()", 
               "<h3>PROCESSED DATA PREVIEW</h3>" + proc_df.head(10).round(4).to_html(classes='p-table'))

        return clean_json({
            "steps": steps,
            "db": {
                "kpis": [
                    {"l": "Total Rows", "v": f"{len(df):,}"},
                    {"l": "Features", "v": str(len(df.columns))},
                    {"l": "Missing Values", "v": f"{(df.isna().sum().sum() / df.size * 100):.1f}%"},
                    {"l": "Model Score", "v": f"{score:.3f} ({metric})"},
                    {"l": "Target", "v": target},
                ],
                "importance": imp,
                "strategy": [
                    {"t": "Key Driver", "d": f"**{imp[0]['name']}** has highest impact."},
                    {"t": "Data Quality", "d": f"{df.isna().sum().sum()} missing values handled."}
                ],
                "processed": proc_df.head(10).round(4).to_dict(orient='records')
            }
        })

    except Exception as e:
        plt.close('all')
        gc.collect()
        logger.error(traceback.format_exc())
        return {"error": True, "message": str(e), "trace": traceback.format_exc()}
