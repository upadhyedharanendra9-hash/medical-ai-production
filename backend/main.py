import io, base64, traceback, logging, gc, os, time
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import LabelEncoder

# --- KERNEL CONFIG ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nexus_kernel")
plt.switch_backend('Agg') # Thread-safe for cloud servers

app = FastAPI()

# CRITICAL: This allows your frontend to communicate with Render
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

@app.get("/")
async def health_check():
    return {"status": "Kernel Online", "node": "Render-Production"}

@app.post("/analyze")
async def analyze_pipeline(file: UploadFile = File(...)):
    user_logs = []
    steps = []
    
    def log_event(msg):
        ts = time.strftime('%H:%M:%S')
        user_logs.append(f"[{ts}] {msg}")
        logger.info(msg)

    try:
        log_event(f"Node Ingesting: {file.filename}")
        content = await file.read()
        
        # 1. Load Data
        df = pd.read_csv(io.BytesIO(content), sep=None, engine='python', on_bad_lines='skip')
        steps.append({"id": 1, "title": "Data Ingestion", "cmd": "pd.read_csv()", "out": df.head(3).to_html(), "pct": 20})
        log_event(f"Success: {len(df)} rows loaded.")

        # 2. Setup Target
        target = df.columns[-1]
        is_cls = df[target].nunique() <= 10
        log_event(f"Target logic set to: {'Classification' if is_cls else 'Regression'}")

        # 3. Visualization
        plt.figure(figsize=(8,4))
        if is_cls: sns.countplot(x=df[target], palette='viridis')
        else: sns.histplot(df[target], kde=True)
        steps.append({"id": 2, "title": "Target Analysis", "cmd": "sns.plot()", "img": get_b64(), "pct": 50})

        # 4. Preprocessing & Training
        proc = df.copy().dropna()
        for col in proc.select_dtypes(include=['object']).columns:
            proc[col] = LabelEncoder().fit_transform(proc[col].astype(str))
        
        X = proc.drop(columns=[target])
        y = proc[target]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        
        model = RandomForestClassifier().fit(X_train, y_train) if is_cls else RandomForestRegressor().fit(X_train, y_train)
        score = model.score(X_test, y_test)
        
        log_event("Random Forest training complete.")
        steps.append({"id": 3, "title": "Model Export", "cmd": "RF.fit()", "out": f"Final Score: {score:.4f}", "pct": 100})

        # Memory Cleanup
        gc.collect()
        
        return clean_json({
            "success": True,
            "steps": steps,
            "logs": user_logs,
            "db": {
                "kpis": [{"l": "Rows", "v": len(df)}, {"l": "Features", "v": len(df.columns)}, {"l": "Score", "v": f"{score:.2%}"}],
                "importance": sorted([{"name": c, "val": float(v)} for c, v in zip(X.columns, model.feature_importances_)], key=lambda x: x['val'], reverse=True)[:5]
            }
        })

    except Exception as e:
        err_msg = str(e)
        full_trace = traceback.format_exc()
        log_event(f"CRITICAL ERROR: {err_msg}")
        
        # Save crash to server for you to check
        with open("backend_crash.log", "a") as f:
            f.write(f"\n--- {time.ctime()} ---\n{full_trace}\n")
            
        return {"error": True, "message": err_msg, "logs": user_logs, "trace": full_trace}

if __name__ == "__main__":
    import uvicorn
    # Important: Render provides the port via environment variables
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
