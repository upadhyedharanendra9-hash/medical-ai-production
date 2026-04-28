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

# --- KERNEL SETUP ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nexus_kernel")
plt.switch_backend('Agg') 

app = FastAPI()

# CRITICAL: This allows different laptops (like Piyu's) to talk to your server
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
    # THIS FIXES YOUR "NOT FOUND" ERROR
    return {"status": "online", "message": "Nexus Kernel Handshake Verified"}

@app.post("/analyze")
async def analyze_pipeline(file: UploadFile = File(...)):
    user_logs = []
    def log_event(msg):
        user_logs.append(f"[{time.strftime('%H:%M:%S')}] {msg}")
        logger.info(msg)

    try:
        log_event(f"Node Ingesting: {file.filename}")
        content = await file.read()
        
        # Load and Clean
        df = pd.read_csv(io.BytesIO(content), sep=None, engine='python', on_bad_lines='skip')
        log_event(f"Dataset active: {len(df)} rows found.")

        target = df.columns[-1]
        is_cls = df[target].nunique() <= 10
        
        # Visuals
        plt.figure(figsize=(10,4))
        sns.histplot(df[target], color='#3b82f6')
        plt.title(f"Distribution of {target}")
        plot_b64 = get_b64()

        # Training Engine
        proc = df.copy().dropna()
        for col in proc.select_dtypes(include=['object']).columns:
            proc[col] = LabelEncoder().fit_transform(proc[col].astype(str))
        
        X, y = proc.drop(columns=[target]), proc[target]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        
        model = RandomForestClassifier().fit(X_train, y_train) if is_cls else RandomForestRegressor().fit(X_train, y_train)
        score = model.score(X_test, y_test)
        
        log_event("Success: Model weights optimized.")

        return clean_json({
            "success": True, 
            "logs": user_logs,
            "db": {
                "kpis": [
                    {"l": "Rows", "v": len(df)}, 
                    {"l": "Score", "v": f"{score:.2%}"},
                    {"l": "Mode", "v": "Classifier" if is_cls else "Regressor"}
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
    # Important: Render provides the port. Defaulting to 8000 for local testing.
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
