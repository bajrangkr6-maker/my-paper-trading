from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

app = FastAPI()

# Templates folder configuration (Render safe path)
current_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(current_dir, "templates")
templates = Jinja2Templates(directory=templates_dir)

# Database Setup (Temporary folder use kar rahe hain taaki live server permission error na de)
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
    sell_price = Column(Float, nullable=True) # Open trade ke liye null rahega
    status = Column(String, default="OPEN") # OPEN ya CLOSED
    timestamp = Column(DateTime, default=datetime.utcnow)

class UserWallet(Base):
    __tablename__ = "user_wallet"
    id = Column(Integer, primary_key=True, index=True)
    balance = Column(Float, default=1000000.0) # 10 Lakh Virtual Cash

# Database Tables Create Karna
Base.metadata.create_all(bind=engine)

# ---- ROUTES ----

# 1. Main Dashboard Route
@app.get("/", response_class=HTMLResponse)
def read_dashboard(request: Request):
    db = SessionLocal()
    
    # Check karenge ki wallet pehle se bana hai ya nahi
    wallet = db.query(UserWallet).first()
    if not wallet:
        wallet = UserWallet(balance=1000000.0)
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
    
    # Saare trades nikalenge
    trades = db.query(TradeLog).order_by(TradeLog.id.desc()).all()
    db.close()
    
    # Context data dictionary
    context_data = {
        "balance": wallet.balance, 
        "trades": trades
    }
    
    # FastAPI naye version ke mutabik 'request' ko pehle position par bheja hai
    return templates.TemplateResponse(request, "dashboard.html", context_data)

# 2. Buy/Sell Order Execution Route
@app.post("/api/trade")
def execute_paper_trade(data: dict):
    db = SessionLocal()
    symbol = data.get("symbol", "").upper()
    qty = int(data.get("qty", 0))
    current_market_price = float(data.get("price", 0))
    action = data.get("action", "").upper()

    if not symbol or qty <= 0 or current_market_price <= 0:
        db.close()
        return {"status": "Error", "message": "Kripya saari fields sahi se bharein!"}

    wallet = db.query(UserWallet).first()
    total_value = qty * current_market_price

    if action == "BUY":
        if wallet.balance < total_value:
            db.close()
            return {"status": "Error", "message": "Paisa kam hai! Insufficient Funds."}
        
        # Balance minus karo aur naya trade open karo
        wallet.balance -= total_value
        new_trade = TradeLog(symbol=symbol, qty=qty, buy_price=current_market_price, status="OPEN")
        db.add(new_trade)
    
    elif action == "SELL":
        # Check karenge ki us stock ki koi open position hai ya nahi
        open_position = db.query(TradeLog).filter(TradeLog.symbol == symbol, TradeLog.status == "OPEN").first()
        if not open_position:
            db.close()
            return {"status": "Error", "message": "Aapke paas is stock ki koi open holding nahi hai!"}
        
        # Balance plus karo aur position close karo
        wallet.balance += total_value
        open_position.sell_price = current_market_price
        open_position.status = "CLOSED"
    
    db.commit()
    db.close()
    return {"status": "Success", "message": f"Virtual {action} Order executed successfully!"}
