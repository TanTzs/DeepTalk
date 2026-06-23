import json
import os
import uuid
from datetime import datetime

DATA_FILE = "data/persons.json"


def load_data() -> dict:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"persons": {}, "global_history": []}


def save_data(data: dict):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_person(data: dict, name: str, color: str, chat_records: str, analysis: dict) -> str:
    person_id = str(uuid.uuid4())[:8]
    data["persons"][person_id] = {
        "id": person_id,
        "name": name,
        "color": color,
        "chat_records": chat_records,
        "analysis": analysis,
        "chat_history": [],
        "created_at": datetime.now().isoformat(),
    }
    save_data(data)
    return person_id


def update_chat_records(data: dict, person_id: str, new_records: str):
    """Append new chat records to existing ones."""
    existing = data["persons"][person_id].get("chat_records", "")
    separator = f"\n\n--- 新增记录 {datetime.now().strftime('%Y-%m-%d')} ---\n\n"
    data["persons"][person_id]["chat_records"] = existing + separator + new_records
    save_data(data)


def update_person_analysis(data: dict, person_id: str, analysis: dict):
    data["persons"][person_id]["analysis"] = analysis
    save_data(data)


def update_person_history(data: dict, person_id: str, history: list):
    data["persons"][person_id]["chat_history"] = history
    save_data(data)


def update_global_history(data: dict, history: list):
    data["global_history"] = history
    save_data(data)


def delete_person(data: dict, person_id: str):
    data["persons"].pop(person_id, None)
    save_data(data)
