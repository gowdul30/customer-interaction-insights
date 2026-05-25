"""
Database service — provides persistent storage via MongoDB Atlas.
Falls back to in-memory storage if MONGO_URI is not configured (local dev).
"""
import os
from typing import List, Optional


class DatabaseService:
    def __init__(self):
        mongo_uri = os.environ.get("MONGO_URI")
        if mongo_uri:
            try:
                from pymongo import MongoClient
                self.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
                # Verify connection
                self.client.admin.command('ping')
                self.db = self.client["customer_insights"]
                self.calls_collection = self.db["calls"]
                self.mode = "mongodb"
                print(f"[DB] Connected to MongoDB Atlas. Collection has {self.calls_collection.count_documents({})} calls.")
            except Exception as e:
                print(f"[DB] MongoDB connection failed: {e}. Falling back to in-memory mode.")
                self.mode = "memory"
                self._memory_calls = []
        else:
            print("[DB] MONGO_URI not set. Using in-memory mode (data will not persist across restarts).")
            self.mode = "memory"
            self._memory_calls = []

    def get_all_calls(self) -> List[dict]:
        """Retrieve all call records."""
        if self.mode == "mongodb":
            return list(self.calls_collection.find({}, {"_id": 0}))
        return list(self._memory_calls)

    def insert_call(self, call_data: dict):
        """Insert a single call record."""
        if self.mode == "mongodb":
            # Remove _id if present to avoid duplicate key errors
            data = {k: v for k, v in call_data.items() if k != "_id"}
            self.calls_collection.insert_one(data)
        else:
            self._memory_calls.append(call_data)

    def insert_many_calls(self, calls: List[dict]):
        """Bulk insert call records."""
        if self.mode == "mongodb":
            cleaned = [{k: v for k, v in c.items() if k != "_id"} for c in calls]
            if cleaned:
                self.calls_collection.insert_many(cleaned)
        else:
            self._memory_calls.extend(calls)

    def count(self) -> int:
        """Count total call records."""
        if self.mode == "mongodb":
            return self.calls_collection.count_documents({})
        return len(self._memory_calls)

    def find_by_client(self, client: str) -> List[dict]:
        """Find calls filtered by client name."""
        if self.mode == "mongodb":
            return list(self.calls_collection.find({"client": client}, {"_id": 0}))
        return [c for c in self._memory_calls if c.get("client") == client]

    def find_by_call_id(self, call_id: str) -> Optional[dict]:
        """Find a single call by its ID."""
        if self.mode == "mongodb":
            return self.calls_collection.find_one({"call_id": call_id}, {"_id": 0})
        for c in self._memory_calls:
            if c.get("call_id") == call_id:
                return c
        return None

    def get_distinct_clients(self) -> List[str]:
        """Get list of unique client names."""
        if self.mode == "mongodb":
            return sorted(self.calls_collection.distinct("client"))
        return sorted(set(c.get("client", "Unknown") for c in self._memory_calls))

    def clear_all(self):
        """Delete all call records (used by migration scripts)."""
        if self.mode == "mongodb":
            self.calls_collection.delete_many({})
        else:
            self._memory_calls.clear()
