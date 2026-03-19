import pymongo
from pymongo.errors import ConnectionFailure, OperationFailure
from config.settings import MONGODB_URI, DATABASE_NAME

from typing import Any

class MongoDBDAO:
    _instance = None
    client: Any = None
    db: Any = None
    connected: bool = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(MongoDBDAO, cls).__new__(cls, *args, **kwargs)
            cls._instance.client = None
            cls._instance.db = None
            cls._instance.connected = False
            cls._instance.connect()
        return cls._instance

    def connect(self):
        try:
            self.client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
            # Verify connection
            self.client.admin.command('ping')
            self.db = self.client[DATABASE_NAME]
            self.connected = True
            print("Successfully connected to MongoDB Atlas.")
        except ConnectionFailure:
            self.connected = False
            print("Failed to connect to MongoDB Atlas.")
        except Exception as e:
            self.connected = False
            print(f"An error occurred connecting to MongoDB Atlas: {e}")

    def insert_session(self, session_dict):
        if self.connected:
            try:
                result = self.db.sessions.insert_one(session_dict)
                return result.inserted_id
            except OperationFailure as e:
                print(f"Error inserting session: {e}")
        return None

    def update_session(self, session_id, update_data):
        if self.connected:
             try:
                result = self.db.sessions.update_one({'session_id': session_id}, {'$set': update_data})
                return result.modified_count
             except OperationFailure as e:
                 print(f"Error updating session: {e}")
        return 0

    def insert_volume_event(self, event_dict):
        if self.connected:
            try:
                result = self.db.volume_events.insert_one(event_dict)
                return result.inserted_id
            except OperationFailure as e:
                print(f"Error inserting volume event: {e}")
        return None
