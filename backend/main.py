import io, base64, traceback, logging, gc, asyncio, os, time
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler

# --- CONFIG ---
executor = ThreadPoolExecutor(max_workers=5)
plt.switch_backend('Agg')

app = FastAPI()

# CRITICAL: Allow all origins for network/cloud access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def clean_json(obj):
    if isinstance(obj, dict): return {k: clean_json(v) for k, v in obj.items()}
    elif isinstance(obj, list): return [clean_json(i) for i in obj]
    elif isinstance(obj, (np.integer, np.int64, np.int32)): return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)): 
        return 0.0 if np.isnan(obj) or np.isinf(obj) else float(obj)
    return obj

def get_b64():
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    plt.close('all')
    return base64.b64encode(buf.getvalue()).decode('utf-8')

# --- ENGINE ---
def run_full_analysis(content, filename):
    u_logs = []
    steps = []
    
    def log_u(msg):
        u_logs.append(f"[{time.strftime('%H:%M:%S')}] {msg}")

    def record(sid, title, cmd, out=None, img=None):
        steps.append({"id": sid, "title": title, "cmd": cmd, "out": out, "img": img, "pct": int((sid/18)*100)})

    try:
        log_u(f"Node Initialized: {filename}")
        
        # 1-2. Loading
        df = pd.read_csv(io.BytesIO(content), sep=None, engine='python', on_bad_lines='skip')
        record(1, "Kernel Boot", "sys.init()", "Worker Thread Secured.")
        record(2, "Data Ingestion", "pd.read_csv()", df.head(3).to_html())
        log_u("Step 2: Data Loaded.")

        # 3-8. Exploration
        target = df.columns[-1]
        is_cls = df[target].nunique() <= 10
        record(3, "Discovery", "df.info()", f"{len(df)} rows found.")
        
        plt.figure(figsize=(10,4))
        if is_cls: sns.countplot(x=df[target], palette='Blues')
        else: sns.histplot(df[target])
        record(6, "Target Distribution", "sns.plot()", img=get_b64())
        log_u(f"Step 6: Target identified as {target}")

        # 9-13. Preprocessing
        proc_df = df.copy().dropna()
        for col in proc_df.select_dtypes(include=['object']).columns:
            proc_df[col] = LabelEncoder().fit_transform(proc_df[col].astype(str))
        
        X = proc_df.drop(columns=[target])
        y = proc_df[target]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        record(13, "Partitioning", "train_test_split()", "80/20 Split Created.")
        log_u("Step 13: Data split complete.")

        # 14-18. Modeling
        model = RandomForestClassifier().fit(X_train, y_train) if is_cls else RandomForestRegressor().fit(X_train, y_train)
        score = model.score(X_test, y_test)
        record(14, "Training", "RandomForest.fit()", f"Score: {score:.4f}")
        
        imp = sorted([{"name": col, "val": float(val)} for col, val in zip(X.columns, model.feature_importances_)], 
                     key=lambda x: x['val'], reverse=True)[:10]
        record(17, "Importance", "Top Drivers", out=f"Primary: {imp[0]['name']}")
        record(18, "Export", "Finalized", "Ready.")
        log_u("Analysis Successful.")

        # KPI construction
        db = {
            "kpis": [{"l": "Rows", "v": len(df)}, {"l": "Features", "v": len(df.columns)}, {"l": "Accuracy", "v": f"{score:.2%}"}],
            "importance": imp,
            "processed": proc_df.head(10).to_dict(orient='records')
        }

        gc.collect()
        return clean_json({"success": True, "steps": steps, "logs": u_logs, "db": db})

    except Exception as e:
        full_err = traceback.format_exc()
        # SAVE LOG TO SERVER
        with open("server_crash_log.txt", "a") as f:
            f.write(f"\n--- {time.ctime()} ---\nFile: {filename}\nError: {str(e)}\n{full_err}\n")
        
        return {"error": True, "message": str(e), "logs": u_logs, "trace": full_err}

@app.post("/analyze")
async def analyze_route(file: UploadFile = File(...)):
    content = await file.read()
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, run_full_analysis, content, file.filename)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
