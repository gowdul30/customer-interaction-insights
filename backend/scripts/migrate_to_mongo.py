"""
One-time script to migrate/seed the local calls.json dataset to MongoDB Atlas.
"""
import os
import sys
import json

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from services.db import DatabaseService

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "calls.json")


def main():
    print("🚀 Starting MongoDB Atlas Migration Script...")
    
    db_service = DatabaseService()
    if db_service.mode != "mongodb":
        print("[ERROR] MONGO_URI is not configured in .env or connection failed.")
        print("Please check your MONGO_URI connection string and try again.")
        sys.exit(1)
        
    if not os.path.exists(DATA_PATH):
        print(f"[ERROR] Source calls.json not found at {DATA_PATH}")
        sys.exit(1)
        
    with open(DATA_PATH, "r") as f:
        calls = json.load(f)
        
    print(f"[INFO] Loaded {len(calls)} calls from local calls.json.")
    
    existing_count = db_service.count()
    if existing_count > 0:
        print(f"[INFO] MongoDB Atlas already has {existing_count} documents in the calls collection.")
        # Non-interactive check for container environments
        force = "--force" in sys.argv or os.environ.get("FORCE_MIGRATION") == "true" or not sys.stdin.isatty()
        if force:
            print("[INFO] Clearing existing calls (forced migration)...")
            db_service.clear_all()
        else:
            response = input("Do you want to clear MongoDB Atlas and re-migrate? (y/N): ").strip().lower()
            if response == 'y':
                print("[INFO] Clearing existing calls...")
                db_service.clear_all()
            else:
                print("[SKIP] Keeping existing data. Exiting.")
                return
                
    print("[INFO] Bulk inserting calls to MongoDB Atlas...")
    db_service.insert_many_calls(calls)
    
    final_count = db_service.count()
    print(f"\n✅ Done! Successfully migrated {final_count} calls to MongoDB Atlas.")

if __name__ == "__main__":
    main()
