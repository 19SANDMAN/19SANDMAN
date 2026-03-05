import os
import requests
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

app = FastAPI()

# ===== ENV =====
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")
API_SECRET = os.getenv("API_SECRET")

if not NOTION_TOKEN or not DATABASE_ID or not API_SECRET:
    raise Exception("Missing NOTION_TOKEN, DATABASE_ID or API_SECRET")

# ===== Security =====
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != API_SECRET:
        raise HTTPException(status_code=401, detail="Invalid API token")
    return credentials.credentials

# ===== Notion Headers =====
NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

# ===== Request Model =====
class TradeRequest(BaseModel):
    pair: str
    direction: str
    entry: float
    stop_loss: float
    take_profit: float
    rr: float
    risk: float
    result: str
    note: str | None = None

# ===== Endpoint =====
@app.post("/trade")
def create_trade(data: TradeRequest, token: str = Depends(verify_token)):

    notion_url = "https://api.notion.com/v1/pages"

    payload = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Trade": {"title": [{"text": {"content": data.pair}}]},
            "Pair": {"rich_text": [{"text": {"content": data.pair}}]},
            "Direction": {"select": {"name": data.direction}},
            "Entry": {"number": data.entry},
            "Stop Loss": {"number": data.stop_loss},
            "Take Profit": {"number": data.take_profit},
            "RR": {"number": data.rr},
            "Risk": {"number": data.risk},
            "Result": {"select": {"name": data.result}},
            "Date": {"date": {"start": datetime.now(timezone.utc).isoformat()}},
        },
    }

    if data.note:
        payload["properties"]["Note"] = {
            "rich_text": [{"text": {"content": data.note}}]
        }

    response = requests.post(notion_url, headers=NOTION_HEADERS, json=payload)

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail=response.text)

    return {"status": "Trade saved to Notion"}
