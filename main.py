# main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from utils import check_availability, book_meeting


app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    message = data.get("message", "").lower()

    if "available" in message or "free" in message:
        return {"response": check_availability(message)}
    elif "book" in message or "schedule" in message:
        return {"response": book_meeting(message)}
    else:
        return {"response": "Please mention if you want to check availability or book a meeting."}
