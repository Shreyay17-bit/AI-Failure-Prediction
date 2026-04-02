import pandas as pd
import numpy as np
import pickle
import yaml
import logging
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix

# -----------------------------
# 1. LOGGING SETUP (Industrial Standard)
# -----------------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def train_pipeline(data_path="dataset.csv"):
    logger.info("🚀 Starting Predictive Maintenance Training Pipeline")

    # -----------------------------
    # 2. DATA LOADING & CLEANING
    # -----------------------------
    try:
        df = pd.read_csv(data_path)
    except FileNotFoundError:
        logger.error(f"Dataset not found at {data_path}")
        return

    # Drop non-predictive IDs
    df = df.drop(columns=[col for col in ["UDI", "Product ID"] if col in df.columns])

    # -----------------------------
    # 3. ADVANCED PREPROCESSING
    # -----------------------------
    # We must save the LabelEncoder to decode 'Type' in the App later
    le = LabelEncoder()
    if "Type" in df.columns:
        df["Type"] = le.fit_transform(df["Type"])
        logger.info(f"Encoded 'Type' categories: {list(le.classes_)}")

    X = df.drop("Machine failure", axis=1)
    y = df["Machine failure"]

    # Check for Class Imbalance
    fail_rate = (y.sum() / len(y)) * 100
    logger.info(f"Dataset Failure Rate: {fail_rate:.2f}%")

    X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

    # -----------------------------
    # 4. MODEL TRAINING (Balanced)
    # -----------------------------
    # 'class_weight' is critical for industrial failure prediction
    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=12,
        class_weight="balanced", 
        random_state=42,
        n_jobs=-1 # Use all CPU cores
    )

    logger.info("Training Random Forest Model...")
    model.fit(X_train, y_train)

    # -----------------------------
    # 5. RIGOROUS EVALUATION
    # -----------------------------
    y_pred = model.predict(X_test)
    
    logger.info("\n" + classification_report(y_test, y_pred))
    
    # Calculate Business Metric: Precision vs Recall
    # We care more about RECALL (don't miss a failure) 
    # than PRECISION (don't have false alarms) in industry.

    # -----------------------------
    # 6. ARTIFACT EXPORT (The "Model Package")
    # -----------------------------
    model_package = {
        "model": model,
        "features": list(X.columns),
        "label_encoder": le,
        "metadata": {
            "train_date": datetime.now().strftime("%Y-%m-%d"),
            "accuracy": model.score(X_test, y_test),
            "n_features": len(X.columns)
        }
    }

    with open("model.pkl", "wb") as f:
        pickle.dump(model_package, f)
    
    logger.info("✅ Model Package saved successfully as 'model.pkl'")

if __name__ == "__main__":
    train_pipeline()