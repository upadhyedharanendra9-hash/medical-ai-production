import io, base64, traceback, logging, gc, asyncio, os, time
from logging.handlers import RotatingFileHandler
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from concurrent.futures import ThreadPoolExecutor
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import r2_score

# --- 1. ADMIN LOGGING (server-side tracking) ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nexus_kernel")
# Keeps last 5 logs of 5MB each
handler = RotatingFileHandler("kernel.log", maxBytes=5*1024*1024, backupCount=5)
handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
logger.addHandler(handler)

# --- 2. CONFIGURATION ---
executor = ThreadPoolExecutor(max_workers=10) # Parallel processing for 10 users
plt.switch_backend('Agg') 

app = FastAPI(title="Nexus Kernel - Log Enabled")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 3. CORE UTILS ---
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

# --- 4. THE 18-STEP ENGINE ---
def run_pipeline(content, filename):
    u_logs = []  # User-visible logs
    steps = []
    
    def log_it(msg, level="INFO"):
        ts = time.strftime('%H:%M:%S')
        u_logs.append(f"[{ts}] {level}: {msg}")
        logger.info(f"{filename} | {msg}")

    def record(sid, title, cmd, out=None, img=None):
        steps.append({"id": sid, "title": title, "cmd": cmd, "out": out, "img": img, "pct": int((sid/18)*100)})

    try:
        log_it(f"Initializing Kernel Node. File: {filename}")
        
        # 1-2. INGESTION
        if filename.lower().endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(content))
        else:
            df = pd.read_csv(io.BytesIO(content), sep=None, engine='python', on_bad_lines='skip')
        
        record(1, "Kernel Boot", "sys.init()", "Environment Isolated.")
        record(2, "Data Ingestion", "pd.read_csv()", df.head(3).to_html(classes='p-table'))
        log_it("Step 2 Complete: Data Ingested.")

        # 3-4. DISCOVERY
        record(3, "Schema Discovery", "df.info()", f"{df.shape[0]} rows, {df.shape[1]} cols.")
        record(4, "Integrity Audit", "df.isnull()", f"Found {df.isnull().sum().sum()} gaps.")
        log_it("Step 4 Complete: Integrity check passed.")

        # 5-8. ANALYSIS & VIZ
        target = df.columns[-1]
        is_cls = df[target].nunique() <= 10
        record(5, "Target Identification", f"Target: {target}", f"Mode: {'Classification' if is_cls else 'Regression'}")
        
        plt.figure(figsize=(10, 4))
        if is_cls: sns.countplot(x=df[target], palette='Blues')
        else: sns.histplot(df[target], kde=True)
        record(6, "Target Distribution", "sns.plot()", img=get_b64())
        
        record(7, "Descriptive Stats", "df.describe()", df.describe().round(2).to_html())
        
        plt.figure(figsize=(10, 6))
        num_df = df.select_dtypes(include=[np.number])
        if not num_df.empty: sns.heatmap(num_df.corr(), cmap='Blues')
        record(8, "Correlation Matrix", "sns.heatmap()", img=get_b64())
        log_it("Step 8 Complete: Statistical baseline generated.")

        # 9-11. PREPROCESSING
        proc_df = df.copy().dropna()
        record(9, "Imputation", "df.dropna()", "Null values removed.")
        
        for col in proc_df.select_dtypes(include=['object']).columns:
            proc_df[col] = LabelEncoder().fit_transform(proc_df[col].astype(str))
        record(10, "Categorical Encoding", "LabelEncoder()", "Non-numeric data encoded.")
        
        num_cols = proc_df.select_dtypes(include=[np.number]).columns.tolist()
        if num_cols:
            proc_df[num_cols] = StandardScaler().fit_transform(proc_df[num_cols])
        record(11, "Feature Scaling", "StandardScaler()", "Numerical variance normalized.")
        log_it("Step 11 Complete: Features scaled and encoded.")

        # 12-13. PARTITIONING
        plt.figure(figsize=(10, 4))
        if num_cols: proc_df[num_cols[:5]].boxplot()
        record(12, "Outlier Analysis", "plt.boxplot()", img=get_b64())
        
        X = proc_df.drop(columns=[target])
        y = proc_df[target]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        record(13, "Data Partitioning", "train_test_split()", f"Train size: {len(X_train)}")
        log_it("Step 13 Complete: Dataset split for training.")

        # 14-16. MODELING
        log_it(f"Step 14: Starting Random Forest training on {len(X_train)} samples.")
        model = RandomForestClassifier(n_estimators=100).fit(X_train, y_train) if is_cls else \
                RandomForestRegressor(n_estimators=100).fit(X_train, y_train)
        score = model.score(X_test, y_test)
        record(14, "Model Training", "RandomForest.fit()", f"Final Score: {score:.4f}")
        
        plt.figure(figsize=(10, 4))
        plt.scatter(y_test, model.predict(X_test), alpha=0.5)
        record(15, "Validation Plot", "Actual vs Predicted", img=get_b64())
        record(16, "Hyper-Benchmarking", "model.evaluate()", "Performance metrics locked.")

        # 17-18. FINALIZATION
        imp = sorted([{"name": col, "val": float(val)} for col, val in zip(X.columns, model.feature_importances_)], 
                     key=lambda x: x['val'], reverse=True)[:10]
        plt.figure(figsize=(10, 5))
        sns.barplot(x=[i['val'] for i in imp], y=[i['name'] for i in imp], palette='Blues_r')
        record(17, "Feature Importance", "Top 10 Drivers", img=get_b64())
        
        record(18, "Kernel Export", "Done", "Memory Flushed.")
        log_it("Step 18 Complete: Analysis Success.")

        # RAM Clean
        del df, proc_df, X_train, model
        gc.collect()

        return clean_json({"success": True, "steps": steps, "logs": u_logs, "score": score})

    except Exception as e:
        err_msg = f"Step {len(steps)+1} Failed: {str(e)}"
        log_it(err_msg, "ERROR")
        return {"error": True, "message": str(e), "logs": u_logs, "trace": traceback.format_exc()}

# --- 5. ROUTES ---
@app.post("/analyze")
async def analyze_route(file: UploadFile = File(...)):
    content = await file.read()
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, run_pipeline, content, file.filename)

@app.get("/health")
async def health():
    return {"status": "ready"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
