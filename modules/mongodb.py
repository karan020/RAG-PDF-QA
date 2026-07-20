import os
from datetime import datetime
from typing import Dict, List, Optional

from bson import ObjectId
from pymongo import MongoClient


class MongoDB:
    """Handles MongoDB operations for users, chats, and conversations."""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if MongoDB._initialized:
            return

        self.mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.db_name = os.getenv("MONGO_DB", "rag_chat_db")
        self.client = None
        self.db = None
        self.users = None
        self.chats = None
        self.conversations = None

        try:
            self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=3000)
            self.db = self.client[self.db_name]
            self.users = self.db["users"]
            self.chats = self.db["chats"]
            self.conversations = self.db["conversations"]
            self._create_indexes()
            print(f"MongoDB connected successfully to {self.db_name}")
            MongoDB._initialized = True
        except Exception as exc:
            print(f"MongoDB connection failed: {exc}")
            self.client = None
            self.db = None
            self.users = None
            self.chats = None
            self.conversations = None

    def _create_indexes(self):
        if self.db is None:
            return
        try:
            self.users.create_index("username", unique=True)
            self.users.create_index("email", sparse=True)
            self.chats.create_index([("user_id", 1), ("created_at", -1)])
            self.chats.create_index([("user_id", 1), ("is_active", 1)])
            self.conversations.create_index([("chat_id", 1), ("created_at", 1)])
            self.conversations.create_index("chat_id")
            print("MongoDB indexes created successfully")
        except Exception as exc:
            print(f"MongoDB indexes creation failed: {exc}")

    def get_db_stats(self) -> Dict:
        if self.db is None:
            return {"status": "disconnected"}
        return {
            "status": "connected",
            "database": self.db_name,
            "collections": {
                "users": self.users.count_documents({}),
                "chats": self.chats.count_documents({"is_active": True}),
                "conversations": self.conversations.count_documents({}),
            },
        }

    def create_user(self, username: str, email: str = None) -> Dict:
        if self.db is None:
            raise Exception("MongoDB not connected")

        user_data = {
            "username": username,
            "email": email,
            "chats": [],
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        result = self.users.insert_one(user_data)
        user_data["_id"] = str(result.inserted_id)
        return user_data

    def get_user(self, user_id: str) -> Optional[Dict]:
        if self.db is None:
            return None
        try:
            user = self.users.find_one({"_id": ObjectId(user_id)})
            if user:
                user["_id"] = str(user["_id"])
            return user
        except Exception:
            return None

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        if self.db is None:
            return None
        user = self.users.find_one({"username": username})
        if user:
            user["_id"] = str(user["_id"])
        return user

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        if self.db is None:
            return None
        user = self.users.find_one({"email": email})
        if user:
            user["_id"] = str(user["_id"])
        return user

    def update_user(self, user_id: str, update_data: Dict) -> bool:
        if self.db is None:
            return False
        update_data["updated_at"] = datetime.now()
        result = self.users.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
        return result.modified_count > 0

    def delete_user(self, user_id: str) -> bool:
        if self.db is None:
            return False

        user = self.get_user(user_id)
        if not user:
            return False

        for chat_id in user.get("chats", []):
            self.delete_chat(chat_id)

        result = self.users.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count > 0

    def create_chat(self, user_id: str, name: str, pdf_filename: str, pdf_path: str) -> Dict:
        if self.db is None:
            raise Exception("MongoDB not connected")

        chat_data = {
            "user_id": user_id,
            "name": name,
            "pdf_filename": pdf_filename,
            "pdf_path": pdf_path,
            "conversation_ids": [],
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "is_active": True,
        }
        result = self.chats.insert_one(chat_data)
        chat_id = str(result.inserted_id)
        chat_data["_id"] = chat_id
        
        # Update user's chats array
        try:
            update_result = self.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$push": {"chats": chat_id}, "$set": {"updated_at": datetime.now()}},
            )
            print(f"Created chat {chat_id} for user {user_id}, update result: {update_result.modified_count}")
            
            if update_result.modified_count == 0:
                print(f"Warning: User document not updated. User ID: {user_id}")
                # Check if user exists
                user = self.users.find_one({"_id": ObjectId(user_id)})
                if not user:
                    print(f"User {user_id} not found in database")
        except Exception as e:
            print(f"Error updating user chats: {e}")
            
        return chat_data

    def get_chat(self, chat_id: str) -> Optional[Dict]:
        if self.db is None:
            return None
        try:
            chat = self.chats.find_one({"_id": ObjectId(chat_id)})
            if chat:
                chat["_id"] = str(chat["_id"])
                conversations = list(self.conversations.find({"chat_id": chat_id}).sort("created_at", 1))
                for conv in conversations:
                    conv["_id"] = str(conv["_id"])
                    # Convert datetime to string for JSON serialization
                    if "created_at" in conv and conv["created_at"]:
                        conv["created_at"] = conv["created_at"].isoformat()
                chat["conversations"] = conversations
                # Convert chat datetime fields to string
                if "created_at" in chat and chat["created_at"]:
                    chat["created_at"] = chat["created_at"].isoformat()
                if "updated_at" in chat and chat["updated_at"]:
                    chat["updated_at"] = chat["updated_at"].isoformat()
                print(f"Retrieved chat {chat_id} with {len(conversations)} conversations")
            else:
                print(f"Chat {chat_id} not found")
            return chat
        except Exception as e:
            print(f"Error retrieving chat {chat_id}: {e}")
            return None

    def get_user_chats(self, user_id: str, limit: int = 50) -> List[Dict]:
        if self.db is None:
            return []
        chats = list(self.chats.find({"user_id": user_id, "is_active": True}).sort("updated_at", -1).limit(limit))
        for chat in chats:
            chat["_id"] = str(chat["_id"])
            chat["conversation_count"] = self.conversations.count_documents({"chat_id": str(chat["_id"])})
        return chats

    def rename_chat(self, chat_id: str, new_name: str) -> bool:
        if self.db is None:
            return False
        result = self.chats.update_one({"_id": ObjectId(chat_id)}, {"$set": {"name": new_name, "updated_at": datetime.now()}})
        return result.modified_count > 0

    def delete_chat(self, chat_id: str) -> bool:
        if self.db is None:
            return False
        try:
            chat = self.chats.find_one({"_id": ObjectId(chat_id)})
            if not chat:
                return False
            user_id = chat["user_id"]
            self.chats.update_one({"_id": ObjectId(chat_id)}, {"$set": {"is_active": False, "updated_at": datetime.now()}})
            self.conversations.delete_many({"chat_id": chat_id})
            self.users.update_one({"_id": ObjectId(user_id)}, {"$pull": {"chats": chat_id}, "$set": {"updated_at": datetime.now()}})
            return True
        except Exception:
            return False

    def add_conversation(self, chat_id: str, question: str, answer: str, sources: List[Dict] = None) -> Dict:
        if self.db is None:
            raise Exception("MongoDB not connected")

        conversation_data = {
            "chat_id": chat_id,
            "question": question,
            "answer": answer,
            "sources": sources or [],
            "created_at": datetime.now(),
        }
        result = self.conversations.insert_one(conversation_data)
        conv_id = str(result.inserted_id)
        conversation_data["_id"] = conv_id
        
        # Update chat's conversation_ids array
        update_result = self.chats.update_one(
            {"_id": ObjectId(chat_id)},
            {"$push": {"conversation_ids": conv_id}, "$set": {"updated_at": datetime.now()}},
        )
        
        print(f"Added conversation {conv_id} to chat {chat_id}, update result: {update_result.modified_count}")
        return conversation_data

    def get_chat_conversations(self, chat_id: str, limit: int = 100) -> List[Dict]:
        if self.db is None:
            return []
        conversations = list(self.conversations.find({"chat_id": chat_id}).sort("created_at", 1).limit(limit))
        for conv in conversations:
            conv["_id"] = str(conv["_id"])
        return conversations

    def get_conversation(self, conv_id: str) -> Optional[Dict]:
        if self.db is None:
            return None
        try:
            conv = self.conversations.find_one({"_id": ObjectId(conv_id)})
            if conv:
                conv["_id"] = str(conv["_id"])
            return conv
        except Exception:
            return None

    def delete_conversation(self, conv_id: str) -> bool:
        if self.db is None:
            return False
        try:
            conv = self.conversations.find_one({"_id": ObjectId(conv_id)})
            if not conv:
                return False
            chat_id = conv["chat_id"]
            result = self.conversations.delete_one({"_id": ObjectId(conv_id)})
            if result.deleted_count > 0:
                self.chats.update_one({"_id": ObjectId(chat_id)}, {"$pull": {"conversation_ids": conv_id}})
                return True
            return False
        except Exception:
            return False

    def get_user_chats_summary(self, user_id: str) -> List[Dict]:
        if self.db is None:
            return []
        chats = list(self.chats.find({"user_id": user_id, "is_active": True}).sort("updated_at", -1))
        summary = []
        for chat in chats:
            conv_count = self.conversations.count_documents({"chat_id": str(chat["_id"])})
            # Convert datetime to string for JSON serialization
            created_at = chat["created_at"].isoformat() if chat.get("created_at") else None
            updated_at = chat["updated_at"].isoformat() if chat.get("updated_at") else None
            summary.append(
                {
                    "id": str(chat["_id"]),
                    "name": chat["name"],
                    "pdf_filename": chat["pdf_filename"],
                    "conversation_count": conv_count,
                    "created_at": created_at,
                    "updated_at": updated_at,
                }
            )
        return summary

    def search_conversations(self, chat_id: str, query: str) -> List[Dict]:
        if self.db is None:
            return []
        conversations = list(self.conversations.find({"chat_id": chat_id, "$text": {"$search": query}}).sort("created_at", 1))
        for conv in conversations:
            conv["_id"] = str(conv["_id"])
        return conversations

    def get_recent_conversations(self, user_id: str, limit: int = 10) -> List[Dict]:
        if self.db is None:
            return []
        chats = self.chats.find({"user_id": user_id, "is_active": True})
        chat_ids = [str(chat["_id"]) for chat in chats]
        if not chat_ids:
            return []
        conversations = list(self.conversations.find({"chat_id": {"$in": chat_ids}}).sort("created_at", -1).limit(limit))
        for conv in conversations:
            conv["_id"] = str(conv["_id"])
        return conversations

    def clear_all_data(self) -> bool:
        if self.db is None:
            return False
        self.users.delete_many({})
        self.chats.delete_many({})
        self.conversations.delete_many({})
        return True

    def get_database_info(self) -> Dict:
        if self.db is None:
            return {"status": "disconnected"}
        return {
            "status": "connected",
            "database": self.db_name,
            "collections": {
                "users": self.users.count_documents({}),
                "chats": self.chats.count_documents({}),
                "conversations": self.conversations.count_documents({}),
            },
            "active_chats": self.chats.count_documents({"is_active": True}),
        }


def get_db() -> MongoDB:
    return MongoDB()


__all__ = ["MongoDB", "get_db"]
