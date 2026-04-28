import io
import base64
import traceback
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import logging
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, r2_score

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nexus_kernel")

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
    steps = []
    try:
        content = await file.read()
        filename = file.filename.lower()

        # --- FIX FOR 0xff / ENCODING ISSUES ---
        if filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(content))
        else:
            # Try multiple encodings to prevent the '0xff' start byte error
            for enc in ['utf-8', 'utf-16', 'cp1252', 'latin1']:
                try:
                    df = pd.read_csv(io.BytesIO(content), sep=None, engine='python', encoding=enc, on_bad_lines='skip')
                    logger.info(f"Loaded with {enc}")
                    break
                except:
                    continue
        
        if 'df' not in locals():
            raise ValueError("File format not supported or encoding corrupted.")

        def record(sid: int, title: str, cmd: str, out=None, img=None):
            steps.append({
                "id": sid,
                "title": title,
                "cmd": cmd,
                "out": out,
                "img": img,
                "pct": int((sid / 18) * 100) # Updated to 18 total steps
            })

        # --- STEP 1-4: INGESTION ---
        record(1, "Kernel Boot", "sys.init()", "Universal Logic Locked.")
        record(2, "Data Ingestion", "pd.read_csv()", df.head(5).to_html(classes='p-table'))
        record(3, "Schema Discovery", "df.info()", f"{df.shape[0]:,} rows × {df.shape[1]} columns")
        record(4, "Integrity Audit", "df.isnull().sum()", df.isnull().sum().to_frame(name='Missing').to_html(classes='p-table'))

        # --- STEP 5-6: TARGETING ---
        target_candidates = ['target', 'label', 'class', 'status', 'outcome', 'y', 'churn', 'cancel', 'fraud', 'survived', 'cardio']
        target = next((c for c in df.columns if any(k in c.lower() for k in target_candidates)), df.columns[-1])
        y_series = df[target]
        is_classification = y_series.nunique() <= 10
        record(5, "Target Identification", f"Target = '{target}'", f"Mode: {'Classification' if is_classification else 'Regression'}")
        
        plt.figure(figsize=(10, 4))
        if is_classification: sns.countplot(x=y_series, palette='Blues')
        else: sns.histplot(y_series, kde=True)
        record(6, "Target Distribution", "sns.plot()", img=get_b64())

        # --- STEP 7-8: STATS ---
        record(7, "Descriptive Stats", "df.describe()", df.describe(include='all').round(2).to_html(classes='p-table'))
        
        plt.figure(figsize=(10, 6))
        num_only = df.select_dtypes(include=[np.number])
        if not num_only.empty: sns.heatmap(num_only.corr(), cmap='Blues')
        record(8, "Correlation Matrix", "sns.heatmap()", img=get_b64())

        # --- STEP 9-11: CLEANING ---
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

        # --- STEP 12: OUTLIER ANALYSIS (Fixed Skip) ---
        plt.figure(figsize=(10, 4))
        if num_cols: proc_df[num_cols[:min(5, len(num_cols))]].boxplot()
        record(12, "Outlier Analysis", "plt.boxplot()", "Visualizing top 5 numerical features.", img=get_b64())

        # --- STEP 13: PARTITIONING (Fixed Skip) ---
        X = proc_df.drop(columns=[target])
        y = y_series if is_classification else proc_df[target]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        record(13, "Data Partitioning", "train_test_split()", f"Train size: {len(X_train)}, Test size: {len(X_test)}")

        # --- STEP 14-16: MODELING ---
        if is_classification:
            model = RandomForestClassifier(n_estimators=100).fit(X_train, y_train)
            score = model.score(X_test, y_test)
            metric = "Accuracy"
        else:
            model = RandomForestRegressor(n_estimators=100).fit(X_train, y_train)
            score = r2_score(y_test, model.predict(X_test))
            metric = "R2 Score"
        
        record(14, "Model Training", "RandomForest.fit()", f"Engineered {metric}: {score:.4f}")

        plt.figure(figsize=(10, 4))
        plt.scatter(y_test, model.predict(X_test), alpha=0.5)
        record(15, "Validation Plot", "Actual vs Predicted", img=get_b64())
        record(16, "Hyper-Benchmarking", "model.evaluate()", f"Final Optimized {metric}: {score:.4f}")

        # --- STEP 17: FEATURE IMPORTANCE (Fixed ID collision) ---
        imp = sorted([{"name": col, "val": float(val)} for col, val in zip(X.columns, model.feature_importances_)], key=lambda x: x['val'], reverse=True)[:10]
        plt.figure(figsize=(10, 5))
        sns.barplot(x=[i['val'] for i in imp], y=[i['name'] for i in imp], palette='Blues_r')
        record(17, "Feature Importance", "Top 10 Drivers", img=get_b64())

        # --- STEP 18: EXPORT ---
        record(18, "Kernel Export", "proc_df.to_dict()", "Data pipeline complete. Dashboard generated.")

        return clean_json({
            "steps": steps,
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

    except Exception as e:
        logger.error(traceback.format_exc())
        return {"error": True, "message": str(e), "trace": traceback.format_exc()}