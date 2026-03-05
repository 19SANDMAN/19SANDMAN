import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

app = FastAPI()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")

if not NOTION_TOKEN or not DATABASE_ID:
    raise Exception("Missing NOTION_TOKEN or DATABASE_ID")

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

class TradeRequest(BaseModel):
    pair: str
    direction: str
    risk: float
    rr: float
    result: str
    note: str
    screenshot_url: str | None = None

def calculate_r_multiple(rr: float, result: str) -> float:
    r = result.strip().lower()
    if r == "win":
        return rr
    if r == "loss":
        return -1
    return 0

def validate_rr(rr: float):
    if rr < 1.5:
        raise HTTPException(status_code=400, detail="RR ต่ำกว่า 1.5 ไม่ผ่านกฎระบบ")

@app.post("/trade")
def create_trade(trade: TradeRequest):
    validate_rr(trade.rr)
    r_multiple = calculate_r_multiple(trade.rr, trade.result)

    payload = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Trade": {"title": [{"text": {"content": trade.pair}}]},
            "Pair": {"select": {"name": trade.pair}},
            "Direction": {"select": {"name": trade.direction}},
            "Risk %": {"number": trade.risk},
            "RR": {"number": trade.rr},
            "R Multiple": {"number": r_multiple},
            "Result": {"select": {"name": trade.result}},
            "Date": {"date": {"start": datetime.now(timezone.utc).isoformat()}},
            "Note": {"rich_text": [{"text": {"content": trade.note}}]},
        },
    }

    if trade.screenshot_url:
        payload["properties"]["Screenshot URL"] = {"url": trade.screenshot_url}

    response = requests.post(
        "https://api.notion.com/v1/pages",
        headers=NOTION_HEADERS,
        json=payload,
        timeout=30,
    )

    if response.status_code not in (200, 201):
        print("NOTION ERROR:", response.status_code, response.text)
        raise HTTPException(status_code=response.status_code, detail=response.json())

    return {"status": "success", "r_multiple": r_multiple}

@app.get("/")
def health():
    return {"status": "Trading Automation Running"}
