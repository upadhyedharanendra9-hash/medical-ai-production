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
plt.switch_backend('Agg') 

app = FastAPI()

# FIXED CORS: This allows external laptops to connect to your Render server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
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

# --- ROUTES ---

@app.get("/")
async def root():
    # This route fixes the "Not Found" error when visiting the URL directly
    return {
        "status": "online", 
        "message": "Medical AI Production Kernel is Live",
        "timestamp": time.ctime()
    }

@app.post("/analyze")
async def analyze_pipeline(file: UploadFile = File(...)):
    user_logs = []
    def log_event(msg):
        ts = time.strftime('%H:%M:%S')
        user_logs.append(f"[{ts}] {msg}")
        logger.info(msg)

    try:
        log_event(f"Kernel Ingesting: {file.filename}")
        content = await file.read()
        
        # 1. Load Data
        df = pd.read_csv(io.BytesIO(content), sep=None, engine='python', on_bad_lines='skip')
        log_event(f"Dataset active: {len(df)} rows.")

        # 2. Logic Check
        target = df.columns[-1]
        is_cls = df[target].nunique() <= 10
        
        # 3. Visualization
        plt.figure(figsize=(10,4))
        if is_cls:
            sns.countplot(x=df[target], palette='magma')
        else:
            sns.histplot(df[target], kde=True, color='#ef4444')
        plt.title(f"Clinical Analysis: {target} Distribution")
        plot_b64 = get_b64()

        # 4. Processing & Training
        proc = df.copy().dropna()
        for col in proc.select_dtypes(include=['object']).columns:
            proc[col] = LabelEncoder().fit_transform(proc[col].astype(str))
        
        X, y = proc.drop(columns=[target]), proc[target]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        
        model = RandomForestClassifier().fit(X_train, y_train) if is_cls else RandomForestRegressor().fit(X_train, y_train)
        score = model.score(X_test, y_test)
        
        log_event("Success: Machine Learning weights finalized.")

        return clean_json({
            "success": True, 
            "logs": user_logs,
            "db": {
                "kpis": [
                    {"l": "Total Records", "v": len(df)}, 
                    {"l": "Accuracy Score", "v": f"{score:.2%}"},
                    {"l": "Target Variable", "v": target}
                ],
                "importance": sorted([{"name": c, "val": float(v)} for c, v in zip(X.columns, model.feature_importances_)], key=lambda x: x['val'], reverse=True)[:5]
            },
            "img": plot_b64
        })

    except Exception as e:
        logger.error(traceback.format_exc())
        return {"error": True, "message": str(e), "logs": user_logs}

if __name__ == "__main__":
    import uvicorn
    # Dynamic port binding for Render
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
