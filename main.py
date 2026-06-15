from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

app = FastAPI()

# Templates configuration
current_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(current_dir, "templates")
templates = Jinja2Templates(directory=templates_dir)

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    # Yeh line hamesha sirf login page hi dikhayegi, chahe jo ho jaye!
    return templates.TemplateResponse(request, "login.html")

@app.post("/save_token")
def save_token(token: str = Form(...)):
    # Abhi ke liye hum token save nahi kar rahe, bas page ko refresh kar rahe hain
    return HTMLResponse(content="""
        <html>
            <body style="font-family:sans-serif; text-align:center; padding-top:100px; background:#f9fafb;">
                <h2 style="color:#22c55e;">Token Received Successfully!</h2>
                <p style="color:#6b7280;">Aapka login page bilkul sahi kaam kar raha hai.</p>
                <a href="/" style="color:#3b82f6; text-decoration:none;">Wapas Login Page par jayein</a>
            </body>
        </html>
    """)
