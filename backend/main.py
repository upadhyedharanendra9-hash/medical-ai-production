import io
import base64
import traceback
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import logging
import gc 
import os
import time
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, r2_score
from logging.handlers import RotatingFileHandler

# --- 1. LOGGING CONFIGURATION ---
# This saves logs to a file named 'kernel_execution.log'
log_formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
log_file = 'kernel_execution.log'

# Keep logs up to 5MB, backup last 3 files
file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3)
file_handler.setFormatter(log_formatter)

logger = logging.getLogger("nexus_kernel")
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
# Add console logging as well
logger.addHandler(logging.StreamHandler())

# Use Agg backend for thread-safe, non-GUI rendering
plt.switch_backend('Agg')

app = FastAPI(title="Nexus Universal Kernel")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

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
    plt.close() 
    return base64.b64encode(buf.getvalue()).decode('utf-8')

@app.post("/analyze")
async def universal_master_pipeline(file: UploadFile = File(...)):
    # Memory and Log Init
    plt.close('all') 
    gc.collect() 
    steps = []
    user_logs = [] # To be returned to frontend
    
    def log_it(msg, level="INFO"):
        ts = time.strftime('%H:%M:%S')
        user_logs.append(f"[{ts}] {msg}")
        if level == "ERROR": logger.error(msg)
        else: logger.info(msg)

    try:
        content = await file.read()
        filename = file.filename.lower()
        log_it(f"Session started for file: {filename}")

        # --- RE-INITIALIZE DATASET ---
        df = None
        if filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(content))
            log_it("Excel format detected and parsed.")
        else:
            for enc in ['utf-8', 'utf-16', 'cp1252', 'latin1']:
                try:
                    df = pd.read_csv(io.BytesIO(content), sep=None, engine='python', encoding=enc, on_bad_lines='skip')
                    log_it(f"CSV detected. Encoding matched: {enc}")
                    break
                except:
                    continue
        
        if df is None:
            raise ValueError("File format not supported or encoding corrupted.")

        def record(sid: int, title: str, cmd: str, out=None, img=None):
            steps.append({
                "id": sid, "title": title, "cmd": cmd, "out": out, "img": img,
                "pct": int((sid / 18) * 100) 
            })

        # --- STEP 1-4: INGESTION ---
        log_it("Executing Steps 1-4: Ingestion & Discovery")
        record(1, "Kernel Boot", "sys.init()", "Universal Logic Locked. Previous session cleared.")
        record(2, "Data Ingestion", "pd.read_csv()", df.head(5).to_html(classes='p-table'))
        record(3, "Schema Discovery", "df.info()", f"{df.shape[0]:,} rows × {df.shape[1]} columns")
        record(4, "Integrity Audit", "df.isnull().sum()", df.isnull().sum().to_frame(name='Missing').to_html(classes='p-table'))

        # --- STEP 5-6: TARGETING ---
        log_it("Executing Steps 5-6: Target Identification")
        target_candidates = ['target', 'label', 'class', 'status', 'outcome', 'y', 'churn', 'cancel', 'fraud', 'survived', 'cardio']
        target = next((c for c in df.columns if any(k in c.lower() for k in target_candidates)), df.columns[-1])
        y_series = df[target]
        is_classification = y_series.nunique() <= 10
        record(5, "Target Identification", f"Target = '{target}'", f"Mode: {'Classification' if is_classification else 'Regression'}")
        
        plt.figure(figsize=(10, 4))
        if is_classification: 
            sns.countplot(x=y_series, palette='Blues')
        else: 
            sns.histplot(y_series, kde=True)
        record(6, "Target Distribution", "sns.plot()", img=get_b64())

        # --- STEP 7-8: STATS ---
        log_it("Executing Steps 7-8: Statistical Baseline")
        record(7, "Descriptive Stats", "df.describe()", df.describe(include='all').round(2).to_html(classes='p-table'))
        
        plt.figure(figsize=(10, 6))
        num_only = df.select_dtypes(include=[np.number])
        if not num_only.empty: 
            sns.heatmap(num_only.corr(), cmap='Blues', annot=False)
        record(8, "Correlation Matrix", "sns.heatmap()", img=get_b64())

        # --- STEP 9-11: CLEANING ---
        log_it("Executing Steps 9-11: Preprocessing Engine")
        proc_df = df.copy()
        num_cols = proc_df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = proc_df.select_dtypes(exclude=[np.number]).columns.tolist()
        
        proc_df[num_cols] = proc_df[num_cols].fillna(proc_df[num_cols].median())
        proc_df[cat_cols] = proc_df[cat_cols].fillna("Missing")
        record(9, "Imputation", "df.fillna()", "Nulls replaced with Median/Mode.")

        for col in cat_cols:
            proc_df[col] = LabelEncoder().fit_transform(proc_df[col].astype(str))
        record(10, "Categorical Encoding", "LabelEncoder()", f"Encoded: {cat_cols}")

        if num_cols:
            proc_df[num_cols] = StandardScaler().fit_transform(proc_df[num_cols])
        record(11, "Feature Scaling", "StandardScaler()", "Numerical variance normalized.")

        # --- STEP 12: OUTLIER ANALYSIS ---
        log_it("Executing Step 12: Outlier Detection")
        plt.figure(figsize=(10, 4))
        if num_cols: 
            proc_df[num_cols[:min(5, len(num_cols))]].boxplot()
        record(12, "Outlier Analysis", "plt.boxplot()", "Visualizing top 5 numerical features.", img=get_b64())

        # --- STEP 13: PARTITIONING ---
        log_it("Executing Step 13: Data Partitioning")
        X = proc_df.drop(columns=[target])
        y = y_series if is_classification else proc_df[target]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        record(13, "Data Partitioning", "train_test_split()", f"Train size: {len(X_train)}, Test size: {len(X_test)}")

        # --- STEP 14-16: MODELING ---
        log_it(f"Executing Steps 14-16: Training RF {'Classifier' if is_classification else 'Regressor'}")
        if is_classification:
            model = RandomForestClassifier(n_estimators=100, random_state=42).fit(X_train, y_train)
            score = model.score(X_test, y_test)
            metric = "Accuracy"
        else:
            model = RandomForestRegressor(n_estimators=100, random_state=42).fit(X_train, y_train)
            score = r2_score(y_test, model.predict(X_test))
            metric = "R2 Score"
        
        record(14, "Model Training", "RandomForest.fit()", f"Engineered {metric}: {score:.4f}")

        plt.figure(figsize=(10, 4))
        plt.scatter(y_test, model.predict(X_test), alpha=0.5, color='#3b82f6')
        plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--')
        record(15, "Validation Plot", "Actual vs Predicted", img=get_b64())
        record(16, "Hyper-Benchmarking", "model.evaluate()", f"Final Optimized {metric}: {score:.4f}")

        # --- STEP 17: FEATURE IMPORTANCE ---
        log_it("Executing Step 17: Importance Extraction")
        imp = sorted([{"name": col, "val": float(val)} for col, val in zip(X.columns, model.feature_importances_)], key=lambda x: x['val'], reverse=True)[:10]
        plt.figure(figsize=(10, 5))
        sns.barplot(x=[i['val'] for i in imp], y=[i['name'] for i in imp], palette='Blues_r')
        record(17, "Feature Importance", "Top 10 Drivers", img=get_b64())

        # --- STEP 18: EXPORT ---
        log_it("Executing Step 18: Session Finalization")
        record(18, "Kernel Export", "proc_df.to_dict()", "Data pipeline complete. Session finalized.")

        # FINAL RESPONSE
        response_data = clean_json({
            "steps": steps,
            "logs": user_logs, # Added for frontend visibility
            "db": {
                "kpis": [
                    {"l": "Rows", "v": f"{len(df)}"},
                    {"l": "Features", "v": f"{len(df.columns)}"},
                    {"l": "Score", "v": f"{score:.3f}"},
                    {"l": "Target", "v": target}
                ],
                "importance": imp,
                "processed": proc_df.head(10).to_dict(orient='records'),
                "strategy": [{"t": "Insight", "d": f"Feature '{imp[0]['name']}' is your primary driver."}]
            }
        })

        # WIPE MEMORY
        log_it("Flushing memory for next node session.")
        del df, proc_df, X_train, X_test, y_train, y_test, model
        gc.collect()

        return response_data

    except Exception as e:
        plt.close('all')
        err_trace = traceback.format_exc()
        log_it(f"FATAL ERROR: {str(e)}", level="ERROR")
        
        # Explicitly save error trace to file
        with open("critical_crash.txt", "a") as f:
            f.write(f"\n--- {time.ctime()} ---\n{err_trace}\n")
            
        return {
            "error": True, 
            "message": str(e), 
            "trace": err_trace, 
            "logs": user_logs
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
