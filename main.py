from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# DATABASE CONFIGURATION: Live server par PostgreSQL ka URL use hoga, local ke liye SQLite fallback hai
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./live_paper_trading.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ---- DATABASE MODELS ----
class TradeLog(Base):
    __tablename__ = "trade_book"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, nullable=False)
    qty = Column(Integer, nullable=False)
    buy_price = Column(Float, nullable=False)
    sell_price = Column(Float, nullable=True) # Open position ke liye null rahega
    status = Column(String, default="OPEN") # OPEN ya CLOSED
    timestamp = Column(DateTime, default=datetime.utcnow)

class UserWallet(Base):
    __tablename__ = "user_wallet"
    id = Column(Integer, primary_key=True, index=True)
    balance = Column(Float, default=1000000.0) # 10 Lakh Virtual Cash

Base.metadata.create_all(bind=engine)

# ---- UPSTOX CONFIGURATION ----
UPSTOX_API_KEY = os.getenv("UPSTOX_API_KEY", "YOUR_UPSTOX_API_KEY")
UPSTOX_ACCESS_TOKEN = os.getenv("UPSTOX_ACCESS_TOKEN", "YOUR_LIVE_ACCESS_TOKEN")

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
    
    # Fetch Trade Book (Saare trades) aur Active Positions (P&L ke liye)
    trades = db.query(TradeLog).order_by(TradeLog.id.desc()).all()
    db.close()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "balance": wallet.balance, 
        "trades": trades
    })

@app.post("/api/trade")
def execute_paper_trade(data: dict):
    db = SessionLocal()
    symbol = data.get("symbol").upper()
    qty = int(data.get("qty"))
    current_market_price = float(data.get("price")) # Upstox Live feed se mila price
    action = data.get("action").upper() # BUY ya SELL

    wallet = db.query(UserWallet).first()
    total_value = qty * current_market_price

    if action == "BUY":
        if wallet.balance < total_value:
            db.close()
            raise HTTPException(status_code=400, detail="Paisa kam hai! Insufficient Funds.")
        
        wallet.balance -= total_value
        new_trade = TradeLog(symbol=symbol, qty=qty, buy_price=current_market_price, status="OPEN")
        db.add(new_trade)
    
    elif action == "SELL":
        # Check karenge ki kya hamare paas open position hai sell karne ke liye
        open_position = db.query(TradeLog).filter(TradeLog.symbol == symbol, TradeLog.status == "OPEN").first()
        if not open_position:
            db.close()
            raise HTTPException(status_code=400, detail="Aapke paas is stock ki koi open holding nahi hai!")
        
        wallet.balance += total_value
        open_position.sell_price = current_market_price
        open_position.status = "CLOSED"
    
    db.commit()
    db.close()
    return {"status": "Success", "message": f"Virtual {action} successful!"}