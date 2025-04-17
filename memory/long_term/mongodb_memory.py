from typing import Dict, List, Any, Optional
import pymongo
from pymongo import MongoClient
from memory import memory_interface
from config.settings import MONGODB_URI, MONGODB_DB, MONGODB_COLLECTION

class MongoDBMemory(memory_interface):

    def __init__(self):
        self._client = MongoClient(MONGODB_URI)
        self._db = self._client[MONGODB_DB]
        self._collection = self._db[MONGODB_COLLECTION]

        self._collection.create_index("_id")

    def save(self, key : str, data : Dict[str,Any]) -> bool:
        try:
            document = {"_id": key,**data}

            self._collection.replace_one({"_id":key},document,upsert=True)
            return True
        except Exception:
            return False
        
    def load(self, key : str) -> Optional[Dict[str,Any]]:
        try:
            document = self._collection.find_one({"_id":key})
            if document:
                document.pop("_id", None)
                return document
            return None
        except Exception:
            return None
    
    def delete(self, key : str) -> bool:
        try:
            result = self._collection.delete_one({"_id":key})
            return result.deleted_count > 0
        except Exception:
            return False
        
    def search(self, query : Dict[str,Any]) -> List[Dict[str,Any]]:
        try:
            cursor = self._collection.find(query)
            results = []
            
            for doc in cursor:
                doc.pop("_id",None)
                results.append(doc)
            return results
        except Exception:
            return []