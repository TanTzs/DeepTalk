import uuid
from datetime import datetime
from db import get_supabase


def load_data(username: str) -> dict:
    sb = get_supabase()

    persons_res = sb.table("persons").select("*").eq("owner", username).execute()
    persons = {}
    for p in persons_res.data:
        persons[p["id"]] = {
            "id": p["id"],
            "name": p["name"],
            "color": p["color"],
            "chat_records": p["chat_records"] or "",
            "analysis": p["analysis"] or {},
            "chat_history": p["chat_history"] or [],
            "created_at": p["created_at"],
        }

    gh_res = (
        sb.table("global_history")
        .select("messages")
        .eq("username", username)
        .execute()
    )
    global_history = gh_res.data[0]["messages"] if gh_res.data else []

    return {"persons": persons, "global_history": global_history}


def save_data(username: str, data: dict):
    """Full replace — used for data import."""
    sb = get_supabase()
    sb.table("persons").delete().eq("owner", username).execute()
    for pid, person in data.get("persons", {}).items():
        sb.table("persons").insert({
            "id": pid,
            "owner": username,
            "name": person["name"],
            "color": person.get("color", "#3d6bff"),
            "chat_records": person.get("chat_records", ""),
            "analysis": person.get("analysis", {}),
            "chat_history": person.get("chat_history", []),
            "created_at": person.get("created_at", datetime.now().isoformat()),
        }).execute()
    sb.table("global_history").upsert({
        "username": username,
        "messages": data.get("global_history", []),
    }).execute()


def add_person(username: str, data: dict, name: str, color: str,
               chat_records: str, analysis: dict) -> str:
    sb = get_supabase()
    person_id = str(uuid.uuid4())[:8]
    row = {
        "id": person_id,
        "owner": username,
        "name": name,
        "color": color,
        "chat_records": chat_records,
        "analysis": analysis,
        "chat_history": [],
        "created_at": datetime.now().isoformat(),
    }
    sb.table("persons").insert(row).execute()
    data["persons"][person_id] = {k: v for k, v in row.items() if k != "owner"}
    return person_id


def update_chat_records(username: str, data: dict, person_id: str, new_records: str):
    existing = data["persons"][person_id].get("chat_records", "")
    separator = f"\n\n--- 新增记录 {datetime.now().strftime('%Y-%m-%d')} ---\n\n"
    updated = existing + separator + new_records
    data["persons"][person_id]["chat_records"] = updated
    get_supabase().table("persons").update(
        {"chat_records": updated}
    ).eq("id", person_id).execute()


def update_person_analysis(username: str, data: dict, person_id: str, analysis: dict):
    data["persons"][person_id]["analysis"] = analysis
    get_supabase().table("persons").update(
        {"analysis": analysis}
    ).eq("id", person_id).execute()


def update_person_history(username: str, data: dict, person_id: str, history: list):
    data["persons"][person_id]["chat_history"] = history
    get_supabase().table("persons").update(
        {"chat_history": history}
    ).eq("id", person_id).execute()


def update_global_history(username: str, data: dict, history: list):
    data["global_history"] = history
    get_supabase().table("global_history").upsert(
        {"username": username, "messages": history}
    ).execute()


def delete_person(username: str, data: dict, person_id: str):
    data["persons"].pop(person_id, None)
    get_supabase().table("persons").delete().eq("id", person_id).execute()
