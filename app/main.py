from fastapi import FastAPI, Request, Query
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta
from typing import Dict
import threading
import time

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Хранилище привязок
bindings: Dict[str, Dict] = {}
lock = threading.Lock()


def cleanup_expired_bindings():
    while True:
        time.sleep(60)
        now = datetime.now()
        with lock:
            expired = [ip for ip, data in bindings.items() if data["expires_at"] < now]
            for ip in expired:
                del bindings[ip]


cleanup_thread = threading.Thread(target=cleanup_expired_bindings, daemon=True)
cleanup_thread.start()


@app.get("/")
async def index(
    request: Request,
    hostname: str = Query(None, description="Имя компьютера"),
    ttl: int = Query(60, description="Время жизни в секундах", ge=1, le=86400)
):
    # Определяем IP
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    else:
        client_ip = request.headers.get("X-Real-IP")
    
    if not client_ip:
        client_ip = request.client.host
    
    # Если передан hostname - сохраняем
    if hostname:
        expires_at = datetime.now() + timedelta(seconds=ttl)
        with lock:
            bindings[client_ip] = {"name": hostname, "expires_at": expires_at}
    
    # Проверяем существующую привязку
    computer_name = "not mentioned"
    with lock:
        if client_ip in bindings and bindings[client_ip]["expires_at"] > datetime.now():
            computer_name = bindings[client_ip]["name"]
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "client_ip": client_ip,
            "computer_name": computer_name
        }
    )
