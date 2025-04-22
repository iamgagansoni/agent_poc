from loguru import logger
from pymongo import MongoClient
import json
from config.settings import IP_V4

class Logging:
    def __init__(self, MONGODB_URI, MONGODB_LOG_DB, MONGODB_LOG_COLLECTION):
        self._client = MongoClient(MONGODB_URI)
        self._db = self._client[MONGODB_LOG_DB]
        self._collection = self._db[MONGODB_LOG_COLLECTION]

        self._collection.create_index("timestamp")

        try:
            self._client.admin.command('ping')
            logger.info("Connected to MongoDB successfuly")
        except Exception as e:
            logger.error(f"MongoDB connection error: {e}")
    
    def setup_logger(self):
        logger.remove()
        logger.add(lambda msg: print(msg), level="INFO")
        logger.add(self.log_to_db, level="DEBUG", serialize=True)
        
        return logger
    
    def log_to_db(self, record):
        try:
            if isinstance(record, str):
                record = json.loads(record)
            
            log_data = record.get("record", {})
            
            log_entry = {
                "timestamp": log_data.get("time", {}).get("repr"),
                "host": IP_V4,
                "level": log_data.get("level", {}).get("name"),
                "message": log_data.get("message"),
                "file": log_data.get("file", {}).get("name"),
                "function": log_data.get("function"),
                "line": log_data.get("line"),
                "context": log_data.get("extra", {})
            }
            
            log_entry = {k: v for k, v in log_entry.items() if v is not None}
            
            self._collection.insert_one(log_entry)
        except Exception as e:
            print(f"Error writing log to MongoDB: {e}")
    
    def close(self):
        if self._client:
            self._client.close()