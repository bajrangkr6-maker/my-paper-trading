from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import requests
import os

app = FastAPI()

# Templates configuration
current_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(current_dir, "templates")
templates = Jinja2Templates(directory=templates_dir)

# Repository ke andar ki token.txt ka path
TOKEN_FILE_PATH = os.path.join(current_dir, "token.txt")

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    # 1. token.txt file ko padhein
    token = ""
    if os.path.exists(TOKEN_FILE_PATH):
        with open(TOKEN_FILE_PATH, "r") as f:
            token = f.read().strip()

    # 2. MANUAL CHECK: Agar file khali hai, toh seedhe Login Page dikhao
    if not token:
        return templates.TemplateResponse(request, "login.html")

    # 3. Agar file mein token hai, toh Upstox se data lekar Dashboard dikhao
    instrument_key = "NSE_EQ|INE002A01018"  # RELIANCE
    url = f"https://api.upstox.com/v2/market-quote/ltp?instrument_key={instrument_key}"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            live_price = data['data'][instrument_key]['last_price']
            
            # Agar dashboard file dubara bana li hai toh dashboard dikhega
            # Varna ek simple confirmation screen dikha dega
            return HTMLResponse(content=f"""
                <html>
                    <head><script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script></head>
                    <body class="bg-gray-900 text-white flex flex-col items-center justify-center h-screen font-sans">
                        <div class="bg-gray-800 p-8 rounded-2xl shadow-xl border border-gray-700 text-center max-w-sm w-full">
                            <span class="text-xs bg-green-500/20 text-green-400 px-2.5 py-1 rounded-full font-bold animate-pulse">● Live From GitHub File</span>
                            <h2 class="text-xl font-bold text-orange-500 mt-4">RELIANCE</h2>
                            <p class="text-4xl font-extrabold mt-2 text-green-400">₹{live_price}</p>
                            <p class="text-xs text-gray-400 mt-4">Aapka token GitHub ki <b>token.txt</b> file se live chal raha hai.</p>
                        </div>
                    </body>
                </html>
            """)
        else:
            # Agar token expire ya galat hai, toh batayega ki file check karo
            return HTMLResponse(content=f"""
                <body style="font-family:sans-serif; text-align:center; padding-top:100px; background:#f9fafb;">
                    <h2 style="color:#ef4444;">Upstox API Error ({response.status_code})</h2>
                    <p>Aapka 'token.txt' mein likha token expired ya galat hai. Kripya GitHub par jaakar naya token daliye.</p>
                </body>
            """)
    except Exception as e:
        return HTMLResponse(content=f"<h3>Connection Error: {str(e)}</h3>")
