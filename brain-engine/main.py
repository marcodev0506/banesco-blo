import sys, os
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
import httpx

# Asegurar que Docker vea los archivos locales
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import database, models, services, agent_service

app = FastAPI(title="Banesco BLO - Inteligencia de Liquidez")

# 1. Configuración de Templates (Indispensable para el Dashboard)
templates = Jinja2Templates(directory="templates")

# 2. Evento Único de Inicio
@app.on_event("startup")
def startup():
    database.init_db()

# 3. CU01: Crear Regla con terminología amigable (Saldo)
@app.post("/rules")
def create_rule(user_id:str, name:str, saldo:float, urgencia:float = 2.0, db:Session=Depends(database.get_db)):
    rule = models.LiquidityRule(
        user_id=user_id, 
        name=name, 
        saldo_minimo=saldo, 
        umbral_urgencia=urgencia
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule

# 4. CU02: Evaluación con IA de Volatilidad
@app.get("/agent/evaluate")
async def evaluate(db: Session = Depends(database.get_db)):
    # Scraping real del BCV
    tasa_actual = await services.RateProvider.get_best_rate()
    
    # Calcular variación respecto a la última revisión
    ultima_log = db.query(models.RateHistory).order_by(models.RateHistory.timestamp.desc()).first()
    diferencia = tasa_actual - ultima_log.rate_value if ultima_log else 0
    
    # Guardar en el histórico para que la IA aprenda
    new_history = models.RateHistory(rate_value=tasa_actual, rate_delta=diferencia)
    db.add(new_history)
    db.commit()

    # Llamar al Agente de IA para detectar anomalías
    ai_assessment = agent_service.VolatilityAgent.train_and_assess_risk(db, diferencia)
    
    rules = db.query(models.LiquidityRule).filter(models.LiquidityRule.is_active == True).all()
    results = []
    
    async with httpx.AsyncClient() as client:
        for r in rules:
            saldo_en_cuenta = 25000.0 # Simulación de balance
            es_emergencia_ai = ai_assessment["is_anomaly"]
            tiene_saldo = saldo_en_cuenta >= r.saldo_minimo

            status_audit = "ESPERAR"
            if tiene_saldo and es_emergencia_ai:
                try:
                    # Orden al Bank Bridge (Node.js)
                    await client.post("http://bank-bridge:3000/execute", json={"amount": r.saldo_minimo})
                    status_audit = "COMPRA_URGENTE_IA"
                except:
                    status_audit = "FALLO_CONEXION"
                
                # Registro inmutable de auditoría
                audit = models.TransactionAudit(
                    rule_id=r.id,
                    status=status_audit,
                    amount_bs=r.saldo_minimo,
                    rate_applied=tasa_actual
                )
                db.add(audit)
                db.commit()
                results.append({"regla": r.name, "accion": "EJECUTADO", "ia_assessment": ai_assessment})
            else:
                results.append({"regla": r.name, "accion": "ESPERAR", "ia_assessment": ai_assessment})
                
    return {"tasa_bcv_hoy": tasa_actual, "ia_assessment": ai_assessment, "evaluaciones": results}

# 5. Dashboard Profesional (Verde Banesco)
@app.get("/dashboard", response_class=HTMLResponse)
def serve_dashboard(request: Request, db: Session = Depends(database.get_db)):
    current_rate_log = db.query(models.RateHistory).order_by(models.RateHistory.timestamp.desc()).first()
    rules = db.query(models.LiquidityRule).all()
    audit_logs = db.query(models.TransactionAudit).order_by(models.TransactionAudit.timestamp.desc()).limit(10).all()

    history_logs = db.query(models.RateHistory).order_by(models.RateHistory.timestamp.desc()).limit(7).all()
    rates_graph = [log.rate_value for log in reversed(history_logs)]
    dates_graph = [log.timestamp.strftime("%H:%M") for log in reversed(history_logs)]

    context_data = {
        "request": request,
        "title": "BANESCO BLO - Dashboard de Inteligencia",
        "primary_green": "#007953",
        "accent_red": "#E1261C",
        "current_rate": current_rate_log.rate_value if current_rate_log else 496.83,
        "rules": rules,
        "audit_logs": audit_logs,
        "rates_graph": rates_graph,
        "dates_graph": dates_graph
    }
    
  
    return templates.TemplateResponse(
        request=request, 
        name="dashboard.html", 
        context=context_data
    )