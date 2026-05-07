import sys, os
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import database, models, services, httpx

app = FastAPI(title="Banesco BLO - Inteligencia de Liquidez")

@app.on_event("startup")
def startup(): database.init_db()

# Actualizado con el nombre 'saldo'
@app.post("/rules")
def create_rule(user_id:str, name:str, saldo:float, urgencia:float = 2.0, db:Session=Depends(database.get_db)):
    rule = models.LiquidityRule(
        user_id=user_id, 
        name=name, 
        saldo_minimo=saldo, 
        umbral_urgencia=urgencia
    )
    db.add(rule); db.commit(); db.refresh(rule)
    return rule

@app.get("/agent/evaluate")
async def evaluate(db:Session=Depends(database.get_db)):
    tasa_actual = await services.RateProvider.get_best_rate()
    rules = db.query(models.LiquidityRule).filter(models.LiquidityRule.is_active == True).all()
    results = []
    
    async with httpx.AsyncClient() as client:
        for r in rules:
            diferencia = tasa_actual - r.ultima_tasa_guardada if r.ultima_tasa_guardada > 0 else 0
            
            saldo_en_cuenta = 25000.0 
            
            es_urgente = diferencia >= r.umbral_urgencia
            tiene_saldo = saldo_en_cuenta >= r.saldo_minimo

            if tiene_saldo and es_urgente:
                try:
                    await client.post("http://bank-bridge:3000/execute", json={"amount": r.saldo_minimo})
                    status = "COMPRA_URGENTE"
                    accion = "EJECUTADO"
                except Exception as e:
                    print(f"Error conectando a bank-bridge: {e}")
                    status = "ERROR_CONEXION_BANK"
                    accion = "FALLO_EJECUCION"
                
                audit = models.TransactionAudit(
                    rule_id=r.id, 
                    status=status, 
                    amount_bs=r.saldo_minimo, 
                    rate_applied=tasa_actual
                )
                db.add(audit)
                r.ultima_tasa_guardada = tasa_actual
                db.commit()
                results.append({"regla": r.name, "accion": accion, "motivo": f"Subida crítica de {diferencia:.2f} Bs"})
            else:
                r.ultima_tasa_guardada = tasa_actual
                db.commit()
                results.append({"regla": r.name, "accion": "ESPERAR", "motivo": f"Variación de {diferencia:.2f} Bs (estable)"})
                
    return {"tasa_bcv_hoy": tasa_actual, "evaluaciones": results}