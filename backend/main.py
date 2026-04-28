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

# --- CONFIGURATION ---
executor = ThreadPoolExecutor(max_workers=5)
plt.switch_backend('Agg')

app = FastAPI()

# Enable CORS so your frontend can talk to this server
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

# --- LOG-ENABLED ENGINE ---
def run_full_analysis(content, filename):
    u_logs = []  # Logs to send back to the user's screen
    steps = []
    
    def log_event(msg, level="INFO"):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {level}: {msg}"
        u_logs.append(log_entry)
        print(log_entry) # Also visible in your terminal

    def record(sid, title, cmd, out=None, img=None):
        steps.append({"id": sid, "title": title, "cmd": cmd, "out": out, "img": img, "pct": int((sid/18)*100)})

    try:
        log_event(f"KERNEL START: Processing {filename}")
        
        # 1-2. Ingestion
        df = pd.read_csv(io.BytesIO(content), sep=None, engine='python', on_bad_lines='skip')
        record(1, "Kernel Boot", "sys.init()", "Worker Thread Secured.")
        record(2, "Data Ingestion", "pd.read_csv()", df.head(3).to_html())
        log_event(f"Data Loaded successfully. Shape: {df.shape}")

        # 3-8. Analysis
        target = df.columns[-1]
        is_cls = df[target].nunique() <= 10
        log_event(f"Target Feature: {target} | ML Mode: {'Classification' if is_cls else 'Regression'}")
        
        plt.figure(figsize=(10,4))
        if is_cls: sns.countplot(x=df[target], palette='Blues')
        else: sns.histplot(df[target])
        record(6, "Target Distribution", "sns.plot()", img=get_b64())
        log_event("Statistical visualizations generated.")

        # 9-13. Preprocessing
        log_event("Starting data cleaning and encoding...")
        proc_df = df.copy().dropna()
        for col in proc_df.select_dtypes(include=['object']).columns:
            proc_df[col] = LabelEncoder().fit_transform(proc_df[col].astype(str))
        
        X = proc_df.drop(columns=[target])
        y = proc_df[target]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        log_event("Pre-processing complete. Data split into 80/20.")

        # 14-18. Modeling
        log_event("Training Random Forest Engine...")
        model = RandomForestClassifier().fit(X_train, y_train) if is_cls else RandomForestRegressor().fit(X_train, y_train)
        score = model.score(X_test, y_test)
        record(14, "Model Training", "RandomForest.fit()", f"Validation Score: {score:.4f}")
        
        imp = sorted([{"name": col, "val": float(val)} for col, val in zip(X.columns, model.feature_importances_)], 
                     key=lambda x: x['val'], reverse=True)[:10]
        record(17, "Importance Analysis", "Feature Drivers", out=f"Primary Driver: {imp[0]['name']}")
        record(18, "Export", "Finalized", "Kernel output ready.")
        
        log_event(f"ANALYSIS COMPLETE. Final Accuracy: {score:.2%}")

        db = {
            "kpis": [{"l": "Rows", "v": len(df)}, {"l": "Features", "v": len(df.columns)}, {"l": "Score", "v": f"{score:.2%}"}],
            "importance": imp,
            "strategy": [{"t": "Model Reliability", "d": f"The engine achieved {score:.2%} accuracy on unseen data."}],
            "processed": proc_df.head(10).to_dict(orient='records')
        }

        # Clear memory
        del df, proc_df
        gc.collect()

        return clean_json({"success": True, "steps": steps, "logs": u_logs, "db": db})

    except Exception as e:
        error_trace = traceback.format_exc()
        log_event(f"CRITICAL ERROR: {str(e)}", level="ERROR")
        
        # --- SAVE ERROR TO TXT FILE ---
        with open("kernel_errors.txt", "a") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"TIMESTAMP: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"FILE: {filename}\n")
            f.write(f"ERROR: {str(e)}\n")
            f.write(f"TRACEBACK:\n{error_trace}\n")
            f.write(f"{'='*60}\n")
        
        return {"error": True, "message": str(e), "logs": u_logs, "trace": error_trace}

# --- ROUTES ---
@app.post("/analyze")
async def analyze_route(file: UploadFile = File(...)):
    content = await file.read()
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, run_full_analysis, content, file.filename)

@app.get("/health")
async def health():
    return {"status": "online"}

if __name__ == "__main__":
    import uvicorn
    # Use PORT from environment for deployment, default to 8000 for local
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
