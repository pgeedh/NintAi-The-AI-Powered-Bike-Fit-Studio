"""
Open-BikeFit User Data & Supabase Integration Hook.
Handles local rider profile persistence and prepares Supabase cloud synchronization.
"""

import os
import json
import uuid
import datetime

PROFILES_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
PROFILES_FILE = os.path.join(PROFILES_DIR, "profiles.json")

# Supabase Credentials (Configurable via environment variables or UI)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")


def get_supabase_client():
    """Returns a Supabase client instance if credentials exist, else None."""
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            from supabase import create_client
            return create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception:
            return None
    return None


def init_db():
    """Initializes local storage directory for rider profiles."""
    os.makedirs(PROFILES_DIR, exist_ok=True)
    if not os.path.exists(PROFILES_FILE):
        default_profile = {
            "id": "rider-alex-chen",
            "name": "Alex Chen",
            "email": "alex.chen@example.com",
            "height_cm": 178,
            "inseam_cm": 83,
            "bike_brand": "Specialized Tarmac SL7",
            "discipline": "ROAD",
            "goal": "Balanced Performance (Standard studio benchmark)",
            "flexibility": "Moderate (Standard)",
            "pain_points": ["Front of Knee (Patella / Anterior)", "Lower Back Fatigue"],
            "created_at": datetime.datetime.now().isoformat()
        }
        with open(PROFILES_FILE, "w", encoding="utf-8") as f:
            json.dump({"profiles": [default_profile], "active_profile_id": "rider-alex-chen"}, f, indent=2)


def load_all_profiles() -> list:
    """Loads all saved rider accounts."""
    init_db()
    try:
        with open(PROFILES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("profiles", [])
    except Exception:
        return []


def save_rider_profile(profile_data: dict) -> dict:
    """Saves or updates a rider profile locally and syncs to Supabase if configured."""
    init_db()
    profiles = load_all_profiles()
    
    if "id" not in profile_data or not profile_data["id"]:
        profile_data["id"] = f"rider-{uuid.uuid4().hex[:8]}"
    
    if "created_at" not in profile_data:
        profile_data["created_at"] = datetime.datetime.now().isoformat()
    
    profile_data["updated_at"] = datetime.datetime.now().isoformat()

    # Update existing or append
    updated = False
    for idx, p in enumerate(profiles):
        if p.get("id") == profile_data["id"] or p.get("email") == profile_data.get("email"):
            profile_data["id"] = p["id"]
            profiles[idx] = profile_data
            updated = True
            break
            
    if not updated:
        profiles.append(profile_data)

    with open(PROFILES_FILE, "w", encoding="utf-8") as f:
        json.dump({"profiles": profiles, "active_profile_id": profile_data["id"]}, f, indent=2)

    # Supabase cloud sync hook
    client = get_supabase_client()
    if client:
        try:
            client.table("rider_profiles").upsert(profile_data).execute()
        except Exception as e:
            print(f"[Open-BikeFit DB] Supabase sync notice: {e}")

    return profile_data


def get_active_profile() -> dict:
    """Returns the most recent active profile."""
    init_db()
    profiles = load_all_profiles()
    if profiles:
        return profiles[-1]
    return {
        "id": "rider-default",
        "name": "Rider",
        "email": "rider@example.com",
        "height_cm": 175,
        "inseam_cm": 82,
        "bike_brand": "Road Bike",
        "discipline": "ROAD",
        "goal": "Balanced Performance (Standard studio benchmark)",
        "flexibility": "Moderate (Standard)",
        "pain_points": []
    }
