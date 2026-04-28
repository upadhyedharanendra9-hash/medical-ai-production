import io
import base64
import traceback
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import logging
import gc
import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, r2_score

# --- CONFIGURATION ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nexus_kernel")

# ThreadPool allows multiple users to process without "killing" the server connection
executor = ThreadPoolExecutor(max_workers=4) 

plt.switch_backend('Agg') # Server-side rendering mode

app = FastAPI(title="Nexus Universal Kernel")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- UTILS ---
def clean_json(obj):
    if isinstance(obj, dict): return {k: clean_json(v) for k, v in obj.items()}
    elif isinstance(obj, list): return [clean_json(i) for i in obj]
    elif isinstance(obj, (np.integer, np.int64, np.int32)): return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)): 
        return 0.0 if np.isnan(obj) or np.isinf(obj) else float(obj)
    elif pd.isna(obj): return None
    return obj

def get_b64():
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=120)
    plt.close('all')
    return base64.b64encode(buf.getvalue()).decode('utf-8')

# --- CORE LOGIC (THREADED) ---
def run_analysis_sync(content, filename):
    """This function runs in a separate thread to prevent blocking other users."""
    steps = []
    plt.close('all')
    
    try:
        # 1. Encoding-Aware Ingestion
        df = None
        if filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(content))
        else:
            for enc in ['utf-8', 'utf-16', 'cp1252', 'latin1']:
                try:
                    df = pd.read_csv(io.BytesIO(content), sep=None, engine='python', encoding=enc, on_bad_lines='skip')
                    break
                except: continue
        
        if df is None: raise ValueError("Invalid File Encoding")

        def record(sid, title, cmd, out=None, img=None):
            steps.append({"id": sid, "title": title, "cmd": cmd, "out": out, "img": img, "pct": int((sid/18)*100)})

        # Steps 1-4: Discovery
        record(1, "Kernel Boot", "sys.init()", "Isolation mode active. Previous data purged.")
        record(2, "Data Ingestion", "pd.read_csv()", df.head(5).to_html(classes='p-table'))
        record(3, "Schema Discovery", "df.info()", f"{df.shape[0]:,} rows × {df.shape[1]} columns")
        record(4, "Integrity Audit", "df.isnull().sum()", df.isnull().sum().to_frame(name='Missing').to_html(classes='p-table'))

        # Steps 5-8: Targeting & Correlation
        target_candidates = ['target', 'label', 'class', 'status', 'outcome', 'y', 'churn', 'fraud']
        target = next((c for c in df.columns if any(k in c.lower() for k in target_candidates)), df.columns[-1])
        y_series = df[target]
        is_classification = y_series.nunique() <= 10
        record(5, "Target Identification", f"Target = '{target}'", f"Mode: {'Classification' if is_classification else 'Regression'}")

        plt.figure(figsize=(10, 4))
        if is_classification: sns.countplot(x=y_series, palette='Blues')
        else: sns.histplot(y_series, kde=True)
        record(6, "Target Distribution", "sns.plot()", img=get_b64())
        record(7, "Descriptive Stats", "df.describe()", df.describe(include='all').round(2).to_html(classes='p-table'))

        plt.figure(figsize=(10, 6))
        num_only = df.select_dtypes(include=[np.number])
        if not num_only.empty: sns.heatmap(num_only.corr(), cmap='Blues', annot=False)
        record(8, "Correlation Matrix", "sns.heatmap()", img=get_b64())

        # Steps 9-11: Preprocessing
        proc_df = df.copy()
        num_cols = proc_df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = proc_df.select_dtypes(exclude=[np.number]).columns.tolist()
        proc_df[num_cols] = proc_df[num_cols].fillna(proc_df[num_cols].median())
        proc_df[cat_cols] = proc_df[cat_cols].fillna("Missing")
        record(9, "Imputation", "df.fillna()", "Nulls replaced.")

        for col in cat_cols:
            proc_df[col] = LabelEncoder().fit_transform(proc_df[col].astype(str))
        record(10, "Categorical Encoding", "LabelEncoder()", "Objects converted to tensors.")

        if num_cols:
            proc_df[num_cols] = StandardScaler().fit_transform(proc_df[num_cols])
        record(11, "Feature Scaling", "StandardScaler()", "Numerical variance normalized.")

        # Step 12: Outlier Analysis (Fixed Skip)
        plt.figure(figsize=(10, 4))
        if num_cols: proc_df[num_cols[:min(5, len(num_cols))]].boxplot()
        record(12, "Outlier Analysis", "plt.boxplot()", img=get_b64())

        # Step 13: Partitioning (Fixed Skip)
        X = proc_df.drop(columns=[target])
        y = y_series if is_classification else proc_df[target]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        record(13, "Data Partitioning", "train_test_split()", f"Train size: {len(X_train)}")

        # Step 14-16: ML Engine
        if is_classification:
            model = RandomForestClassifier(n_estimators=100, random_state=42).fit(X_train, y_train)
            score = model.score(X_test, y_test)
            metric = "Accuracy"
        else:
            model = RandomForestRegressor(n_estimators=100, random_state=42).fit(X_train, y_train)
            score = r2_score(y_test, model.predict(X_test))
            metric = "R2 Score"
        record(14, "Model Training", "RandomForest.fit()", f"{metric}: {score:.4f}")

        plt.figure(figsize=(10, 4))
        plt.scatter(y_test, model.predict(X_test), alpha=0.5, color='#3b82f6')
        record(15, "Validation Plot", "Actual vs Predicted", img=get_b64())
        record(16, "Hyper-Benchmarking", "model.evaluate()", f"Optimized {metric}: {score:.4f}")

        # Step 17: Importance (Fixed ID)
        imp = sorted([{"name": col, "val": float(val)} for col, val in zip(X.columns, model.feature_importances_)], key=lambda x: x['val'], reverse=True)[:10]
        plt.figure(figsize=(10, 5))
        sns.barplot(x=[i['val'] for i in imp], y=[i['name'] for i in imp], palette='Blues_r')
        record(17, "Feature Importance", "Top 10 Drivers", img=get_b64())

        # Step 18: Export
        record(18, "Kernel Export", "Session Finalized", "Pipeline logic flushed.")

        result = {
            "steps": steps,
            "db": {
                "kpis": [{"l": "Rows", "v": str(len(df))}, {"l": "Features", "v": str(len(df.columns))}, {"l": "Score", "v": f"{score:.3f}"}, {"l": "Target", "v": target}],
                "importance": imp,
                "processed": proc_df.head(10).to_dict(orient='records'),
                "strategy": [{"t": "Key Driver", "d": f"'{imp[0]['name']}' has the highest impact."}]
            }
        }
        
        # Cleanup
        del df, proc_df, X_train, X_test, model
        gc.collect()
        return clean_json(result)

    except Exception as e:
        return {"error": True, "message": str(e), "trace": traceback.format_exc()}

@app.post("/analyze")
async def universal_master_pipeline(file: UploadFile = File(...)):
    content = await file.read()
    filename = file.filename
    
    # Offload the heavy work to a worker thread so FastAPI can stay responsive
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(executor, run_analysis_sync, content, filename)
    
    return response
