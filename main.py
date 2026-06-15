from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

app = FastAPI()

# Templates directory config
current_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(current_dir, "templates")
templates = Jinja2Templates(directory=templates_dir)

# Database Config (Live Server Safe)
DATABASE_URL = "sqlite:////tmp/live_paper_trading.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ---- DATABASE MODELS ----
class TradeLog(Base):
    __tablename__ = "trade_book"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, nullable=False)
    qty = Column(Integer, nullable=False)
    buy_price = Column(Float, nullable=False)
    sell_price = Column(Float, nullable=True)
    status = Column(String, default="OPEN")
    timestamp = Column(DateTime, default=datetime.utcnow)

class UserWallet(Base):
    __tablename__ = "user_wallet"
    id = Column(Integer, primary_key=True, index=True)
    balance = Column(Float, default=1000000.0)

Base.metadata.create_all(bind=engine)

# ---- ROUTES ----
@app.get("/", response_class=HTMLResponse)
def read_dashboard(request: Request):
    db = SessionLocal()
    wallet = db.query(UserWallet).first()
    if not wallet:
        wallet = UserWallet(balance=1000000.0)
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
    
    trades = db.query(TradeLog).order_by(TradeLog.id.desc()).all()
    db.close()
    
    # Context dictionary ko alag se define kiya taaki Jinja2 error na de
    context_data = {
        "request": request, 
        "balance": wallet.balance, 
        "trades": trades
    }
    
    return templates.TemplateResponse(name="dashboard.html", context=context_data)

@app.post("/api/trade")
def execute_paper_trade(data: dict):
    db = SessionLocal()
    symbol = data.get("symbol", "").upper()
    qty = int(data.get("qty", 0))
    current_market_price = float(data.get("price", 0))
    action = data.get("action", "").upper()

    if not symbol or qty <= 0 or current_market_price <= 0:
        db.close()
        return {"status": "Error", "message": "Galat data bhara hai!"}

    wallet = db.query(UserWallet).first()
    total_value = qty * current_market_price

    if action == "BUY":
        if wallet.balance < total_value:
            db.close()
            return {"status": "Error", "message": "Paisa kam hai! Insufficient Funds."}
        
        wallet.balance -= total_value
        new_trade = TradeLog(symbol=symbol, qty=qty, buy_price=current_market_price, status="OPEN")
        db.add(new_trade)
    
    elif action == "SELL":
        open_position = db.query(TradeLog).filter(TradeLog.symbol == symbol, TradeLog.status == "OPEN").first()
        if not open_position:
            db.close()
            return {"status": "Error", "message": "Aapke paas is stock ki koi open holding nahi hai!"}
        
        wallet.balance += total_value
        open_position.sell_price = current_market_price
        open_position.status = "CLOSED"
    
    db.commit()
    db.close()
    return {"status": "Success", "message": f"Virtual {action} successful!"}
