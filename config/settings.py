import os
from dotenv import load_dotenv
import socket

load_dotenv()

def get_ipv4():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()

#PATH
CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))

# KEYS
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# DAtABASE
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB = os.getenv("MONGODB_DB", "agent_memory")
MONGODB_LOG_DB = os.getenv("MONGODB_LOG_DB","loggingdb")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "conversations")
MONGODB_LOG_COLLECTION = os.getenv("MONGODB_LOG_COLLECTION","multiagentlog")

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "admin@123")
MYSQL_DB = os.getenv("MYSQL_DB", "agent_memory")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))

#Short term memory
SHORT_TERM_MEMORY_EXPIRATION = int(os.getenv("SHORT_TERM_MEMORY_EXPIRATION","3600"))
CACHE_MAX_SIZE = int(os.getenv("CACHE_MAX_SIZE","1000"))

#API CONFIG
API_HOST = os.getenv("API_HOST","0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

#Streamlit
STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", "8501"))

#IP
IP_V4 = get_ipv4()