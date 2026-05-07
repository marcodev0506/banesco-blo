from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class LiquidityRule(Base):
    __tablename__ = "liquidity_rules"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String)
    name = Column(String)
    
    saldo_minimo = Column(Float)        
    umbral_urgencia = Column(Float, default=2.0) 
    ultima_tasa_guardada = Column(Float, default=0.0) 
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class TransactionAudit(Base):
    __tablename__ = "transaction_audit"
    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("liquidity_rules.id"))
    status = Column(String)
    amount_bs = Column(Float)
    rate_applied = Column(Float)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())