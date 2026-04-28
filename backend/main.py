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

# --- SYSTEM CONFIG ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nexus_kernel")

# Thread pool for CPU-bound ML tasks
executor = ThreadPoolExecutor(max_workers=4)
plt.switch_backend('Agg')

app = FastAPI(title="Nexus Universal Kernel - Node")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- CORE UTILS ---
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
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=110)
    plt.close('all')
    return base64.b64encode(buf.getvalue()).decode('utf-8')

# --- PROCESSING ENGINE ---
def run_heavy_analysis(content, filename):
    steps = []
    try:
        # 1. Ingestion
        if filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(content))
        else:
            for enc in ['utf-8', 'utf-16', 'cp1252', 'latin1']:
                try:
                    df = pd.read_csv(io.BytesIO(content), sep=None, engine='python', encoding=enc)
                    break
                except: continue
        
        if 'df' not in locals(): raise ValueError("Decode Failed")

        def record(sid, title, cmd, out=None, img=None):
            steps.append({"id": sid, "title": title, "cmd": cmd, "out": out, "img": img, "pct": int((sid/18)*100)})

        # 2. Kernel Logic (Steps 1-11)
        record(1, "Kernel Boot", "sys.init()", "Worker Instance Active.")
        record(2, "Data Ingestion", "pd.read_csv()", df.head(5).to_html(classes='p-table'))
        record(3, "Schema Discovery", "df.info()", f"{df.shape[0]} rows found.")
        record(4, "Integrity Audit", "df.isnull()", f"Found {df.isnull().sum().sum()} nulls.")

        # ML Target Detection
        target = df.columns[-1]
        y_series = df[target]
        is_classification = y_series.nunique() <= 10
        record(5, "Target Identification", f"Target: {target}", f"Mode: {'Classifier' if is_classification else 'Regressor'}")

        # Visualization
        plt.figure(figsize=(10, 4))
        if is_classification: sns.countplot(x=y_series, palette='Blues')
        else: sns.histplot(y_series, kde=True)
        record(6, "Target Distribution", "sns.plot()", img=get_b64())

        # Preprocessing
        proc_df = df.copy().dropna()
        num_cols = proc_df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = proc_df.select_dtypes(exclude=[np.number]).columns.tolist()
        
        for col in cat_cols:
            proc_df[col] = LabelEncoder().fit_transform(proc_df[col].astype(str))
        if num_cols:
            proc_df[num_cols] = StandardScaler().fit_transform(proc_df[num_cols])
        
        record(11, "Feature Scaling", "StandardScaler()", "Normalization Complete.")

        # Step 12: Outliers
        plt.figure(figsize=(10, 4))
        if num_cols: proc_df[num_cols[:5]].boxplot()
        record(12, "Outlier Analysis", "plt.boxplot()", img=get_b64())

        # Step 13-17: ML Engine
        X = proc_df.drop(columns=[target])
        y = proc_df[target]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        record(13, "Partitioning", "train_test_split()", f"Train size: {len(X_train)}")

        if is_classification:
            model = RandomForestClassifier(n_estimators=100).fit(X_train, y_train)
            score = model.score(X_test, y_test)
        else:
            model = RandomForestRegressor(n_estimators=100).fit(X_train, y_train)
            score = r2_score(y_test, model.predict(X_test))
        
        record(14, "Model Training", "RandomForest", f"Score: {score:.4f}")

        # Importance
        imp = sorted([{"name": col, "val": float(val)} for col, val in zip(X.columns, model.feature_importances_)], 
                     key=lambda x: x['val'], reverse=True)[:10]
        plt.figure(figsize=(10, 5))
        sns.barplot(x=[i['val'] for i in imp], y=[i['name'] for i in imp], palette='Blues_r')
        record(17, "Feature Importance", "Top 10", img=get_b64())

        record(18, "Kernel Export", "Done", "Session Cleared.")

        final_out = clean_json({
            "steps": steps,
            "db": {
                "kpis": [{"l": "Rows", "v": str(len(df))}, {"l": "Score", "v": f"{score:.3f}"}],
                "importance": imp,
                "processed": proc_df.head(10).to_dict(orient='records'),
                "strategy": [{"t": "Insight", "d": f"Primary driver detected: {imp[0]['name']}"}]
            }
        })

        # Memory Cleanup
        del df, proc_df, X_train, X_test, model
        gc.collect()
        return final_out

    except Exception as e:
        logger.error(traceback.format_exc())
        return {"error": True, "message": str(e)}

@app.post("/analyze")
async def universal_master_pipeline(file: UploadFile = File(...)):
    content = await file.read()
    filename = file.filename
    loop = asyncio.get_event_loop()
    # Offload to executor to keep the main thread/port responsive
    return await loop.run_in_executor(executor, run_heavy_analysis, content, filename)

@app.get("/health")
async def health():
    return {"status": "online"}
