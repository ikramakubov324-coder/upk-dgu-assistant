import uuid
import qrcode
from io import BytesIO
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

app = FastAPI(title="УПК: Цифровой помощник")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

tickets = []

class TicketCreate(BaseModel):
    description: str

class StatusUpdate(BaseModel):
    status: str
    assignee: str = ""
    result: str = ""

# --- РОУТЫ СТРАНИЦ ДЛЯ ПОЛЬЗОВАТЕЛЯ И АДМИНА ---

@app.get("/")
def read_index():
    return FileResponse("index.html")

@app.get("/admin")
def read_admin():
    return FileResponse("admin.html")

# --- ГЕНЕРАЦИЯ QR-КОДОВ (Ваша Роль 4) ---
@app.get("/api/qr")
def generate_qr(cabinet: str):
    # При сканировании перенаправляем на форму с параметром кабинета
    target_url = f"https://ref-murray-democratic-thesaurus.trycloudflare.com/?cabinet={cabinet}"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(target_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")

# --- API ДЛЯ РАБОТЫ С ЗАЯВКАМИ ---

@app.post("/api/tickets")
def create_ticket(payload: TicketCreate):
    desc_lower = payload.description.lower()
    
    if "wi-fi" in desc_lower or "вайфай" in desc_lower or "интернет" in desc_lower:
        ai_action = "auto_reply"
        ai_response = "Типовой ответ: Авторизация в Wi-Fi сети колледжа происходит через учетную запись Госуслуг."
        status = "Закрыто ИИ"
    elif "пароль" in desc_lower or "логин" in desc_lower:
        ai_action = "auto_reply"
        ai_response = "Типовой ответ: Сбросить пароль от личного кабинета можно в ИТ-отделе (кабинет 104)."
        status = "Закрыто ИИ"
    else:
        ai_action = "create_ticket"
        ai_response = "Безопасный автоответ невозможен. Требуется вмешательство специалиста."
        status = "Новая"

    ticket = {
        "id": str(uuid.uuid4())[:8],
        "description": payload.description,
        "ai_action": ai_action,
        "ai_response": ai_response,
        "status": status,
        "assignee": "Не назначен" if ai_action == "create_ticket" else "ИИ-Помощник",
        "result": ""
    }
    
    tickets.append(ticket)
    return ticket

@app.get("/api/tickets")
def get_tickets():
    return tickets

@app.put("/api/tickets/{ticket_id}")
def update_ticket(ticket_id: str, payload: StatusUpdate):
    for ticket in tickets:
        if ticket["id"] == ticket_id:
            ticket["status"] = payload.status
            if payload.assignee:
                ticket["assignee"] = payload.assignee
            if payload.result:
                ticket["result"] = payload.result
            return ticket
    raise HTTPException(status_code=404, detail="Заявка не найдена")

if __name__ == "__main__":
    import uvicorn
    import os
    # Автоматически берем имя текущего файла вместо жестко прописанного "main"
    file_name = os.path.basename(__file__).replace(".py", "")
    uvicorn.run(f"{file_name}:app", host="127.0.0.1", port=8000, reload=True)