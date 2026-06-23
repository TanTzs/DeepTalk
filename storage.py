import json
import os
import uuid
from datetime import datetime


def _data_file(username: str) -> str:
    return f"data/{username}/persons.json"


def load_data(username: str) -> dict:
    path = _data_file(username)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"persons": {}, "global_history": []}


def save_data(username: str, data: dict):
    path = _data_file(username)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_person(username: str, data: dict, name: str, color: str, chat_records: str, analysis: dict) -> str:
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
    save_data(username, data)
    return person_id


def update_chat_records(username: str, data: dict, person_id: str, new_records: str):
    existing = data["persons"][person_id].get("chat_records", "")
    separator = f"\n\n--- 新增记录 {datetime.now().strftime('%Y-%m-%d')} ---\n\n"
    data["persons"][person_id]["chat_records"] = existing + separator + new_records
    save_data(username, data)


def update_person_analysis(username: str, data: dict, person_id: str, analysis: dict):
    data["persons"][person_id]["analysis"] = analysis
    save_data(username, data)


def update_person_history(username: str, data: dict, person_id: str, history: list):
    data["persons"][person_id]["chat_history"] = history
    save_data(username, data)


def update_global_history(username: str, data: dict, history: list):
    data["global_history"] = history
    save_data(username, data)


def delete_person(username: str, data: dict, person_id: str):
    data["persons"].pop(person_id, None)
    save_data(username, data)
