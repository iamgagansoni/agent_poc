from typing import Dict, Any, List, Optional
import json
import mysql.connector
from memory.memory_interface import MemoryInterface
from config.settings import MYSQL_HOST, MYSQL_PASSWORD, MYSQL_DB, MYSQL_PORT, MYSQL_USER

class MySQLMemory(MemoryInterface):

    def __init__(self):
        self._conn = mysql.connector.connect(
            host = MYSQL_HOST,
            user = MYSQL_USER,
            password = MYSQL_PASSWORD,
            database = MYSQL_DB,
            port = MYSQL_PORT
        )

        self._create_table()
    
    def _create_table(self):
        cursor = self._conn.cursor()
        cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory (
                id VARCHAR(255) PRIMARY KEY,
                data JSON NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        self._conn.commit()
        cursor.close()
    
    def _ensure_connection(self):
        if not self._conn.is_connected():
            self._conn = mysql.connector.connect(
                host = MYSQL_HOST,
                user = MYSQL_USER,
                password = MYSQL_PASSWORD,
                database = MYSQL_DB,
                port = MYSQL_PORT 
            )

    def save(self, key, data):
        try:
            self._ensure_connection()
            cursor = self._conn.cursor()

            json_data = json.dumps(data)

            cursor.execute("REPLACE INTO memory (id, data) VALUES (%s, %s)",(key, json_data))

            self._conn.commit()
            cursor.close()
            return True
        except Exception:
            return False
    
    def load(self, key):
        try:
            self._ensure_connection()
            cursor = self._conn.cursor(dictionary=True)

            cursor.execute(
                "SELECT data FROM memory Where id = %s",(key,)
            )

            result = cursor.fetchone()
            cursor.close()

            if result:
                return json.loads(result["data"])
            return None
        except Exception:
            return None
    
    def delete(self, key):
        try:
            self._ensure_connection()
            cursor = self._conn.cursor()

            cursor.execute(
                "DELETE FROM memory WHERE id = %s",(key,)
            )

            self._conn.commit()
            successful = cursor.rowcount > 0
            cursor.close()


            return successful
        except Exception:
            return False
        
    def search(self, query):
        try:
            self._ensure_connection()
            cursor = self._conn.cursor(dictionary=True)

            condtitions = []
            params = []

            for key, value in query.items():
                condtitions.append(f"JSON_EXTRACT(data, '$.{key}') = %s")
                params.append(json.dumps(value))
            
            where_clause = " AND ".join(condtitions) if condtitions else "1=1"

            cursor.execute(
                f"SELECT data FROM memory WHERE {where_clause}",tuple(params)
            )

            results = []
            for row in cursor.fetchall():
                results.append(json.loads(row["data"]))

            cursor.close()
            return results
        except Exception:
            return []
        