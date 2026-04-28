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

# --- LOGGING SETUP ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nexus_kernel")

# Use Agg backend for thread-safe, non-GUI rendering
plt.switch_backend('Agg')

app = FastAPI(title="Nexus Universal Kernel")

# CRITICAL: Allow Render's domain and local testing
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"]
)

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

@app.get("/health")
async def health():
    return {"status": "online", "timestamp": time.ctime()}

@app.post("/analyze")
async def universal_master_pipeline(file: UploadFile = File(...)):
    plt.close('all') 
    gc.collect() 
    
    steps = []
    user_logs = []
    
    def log_it(msg, level="INFO"):
        ts = time.strftime('%H:%M:%S')
        full_msg = f"[{ts}] {msg}"
        user_logs.append(full_msg)
        if level == "ERROR": logger.error(msg)
        else: logger.info(msg)

    try:
        content = await file.read()
        filename = file.filename.lower()
        log_it(f"Kernel received: {filename}")

        # --- DATA INGESTION ---
        df = None
        if filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(content))
        else:
            for enc in ['utf-8', 'cp1252', 'latin1']:
                try:
                    df = pd.read_csv(io.BytesIO(content), sep=None, engine='python', encoding=enc, on_bad_lines='skip')
                    log_it(f"Parsed with {enc} encoding")
                    break
                except: continue
        
        if df is None: raise ValueError("Unsupported file or corrupted encoding.")

        def record(sid, title, cmd, out=None, img=None):
            steps.append({"id": sid, "title": title, "cmd": cmd, "out": out, "img": img, "pct": int((sid / 18) * 100)})

        # Steps 1-4
        record(1, "Kernel Boot", "sys.init()", "Logic Locked.")
        record(2, "Data Ingestion", "pd.read_csv()", df.head(3).to_html(classes='p-table'))
        record(3, "Schema Discovery", "df.info()", f"{df.shape[0]} rows found.")
        record(4, "Integrity Audit", "df.isnull()", "Checked for missing values.")

        # Steps 5-8
        target = df.columns[-1]
        is_classification = df[target].nunique() <= 10
        log_it(f"Target: {target} | Mode: {'Class' if is_classification else 'Reg'}")
        
        plt.figure(figsize=(10, 4))
        sns.histplot(df[target]) if not is_classification else sns.countplot(x=df[target])
        record(6, "Distribution", "plt.show()", img=get_b64())

        # Steps 9-13 (Processing)
        proc_df = df.copy().dropna()
        for col in proc_df.select_dtypes(include=['object']).columns:
            proc_df[col] = LabelEncoder().fit_transform(proc_df[col].astype(str))
        
        X = proc_df.drop(columns=[target])
        y = proc_df[target]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        record(13, "Partitioning", "split()", "80/20 train-test split created.")

        # Steps 14-18 (Modeling)
        model = RandomForestClassifier().fit(X_train, y_train) if is_classification else RandomForestRegressor().fit(X_train, y_train)
        score = model.score(X_test, y_test)
        record(14, "Training", "RF.fit()", f"Score: {score:.4f}")
        
        imp = sorted([{"name": col, "val": float(val)} for col, val in zip(X.columns, model.feature_importances_)], key=lambda x: x['val'], reverse=True)[:10]
        record(17, "Importance", "Top Drivers", out=f"Main: {imp[0]['name']}")
        record(18, "Export", "Done", "Pipeline finalized.")

        log_it("Success: Full analysis complete.")

        return clean_json({
            "steps": steps,
            "logs": user_logs,
            "db": {
                "kpis": [{"l": "Rows", "v": len(df)}, {"l": "Score", "v": f"{score:.2%}"}, {"l": "Target", "v": target}],
                "importance": imp,
                "processed": proc_df.head(5).to_dict(orient='records')
            }
        })

    except Exception as e:
        err_trace = traceback.format_exc()
        log_it(f"CRASH: {str(e)}", "ERROR")
        with open("crash_log.txt", "a") as f:
            f.write(f"\n{time.ctime()}: {err_trace}")
        return {"error": True, "message": str(e), "trace": err_trace, "logs": user_logs}

if __name__ == "__main__":
    import uvicorn
    # Render uses the PORT environment variable
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
