import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sqlalchemy.orm import Session
import models

class VolatilityAgent:
    @staticmethod
    def train_and_assess_risk(db: Session, current_delta: float):
        """
        Entrena un modelo simple de Isolation Forest para decidir si 
        la subida actual (delta) es una anomalía de mercado.
        """
        # 1. Obtener historial de variaciones de tasa
        logs = db.query(models.RateHistory).order_by(models.RateHistory.timestamp.desc()).limit(100).all()
        
        if len(logs) < 10:
            # No hay suficientes datos para IA, usamos lógica por defecto
            return {"risk_level": "BAJO", "is_anomaly": False, "suggested_threshold": 2.0}

        # 2. Preparar datos para scikit-learn
        deltas = np.array([log.rate_delta for log in logs]).reshape(-1, 1)
        
        # 3. Entrenar el modelo (Isolation Forest detecta outliers)
        # Contamination 0.05 significa que asumimos que el 5% de saltos son 'emergencias'
        model = IsolationForest(contamination=0.05, random_state=42)
        model.fit(deltas)
        
        # 4. Predecir si la variación actual es una anomalía
        # -1 = Anomalía (outlier), 1 = Normal (inlier)
        prediction = model.predict(np.array([[current_delta]]))[0]
        is_anomaly = True if prediction == -1 else False
        
        # 5. Sugerir un umbral dinámico basado en el percentil 95
        suggested_threshold = np.percentile(deltas, 95)

        return {
            "risk_level": "ALTO" if is_anomaly else "NORMAL",
            "is_anomaly": is_anomaly,
            "suggested_threshold": round(suggested_threshold, 2),
            "model_confidence": "MEDIA (100 pts)"
        }