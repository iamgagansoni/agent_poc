import os
from dotenv import load_dotenv

load_dotenv()

# API
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# DAtABASE
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")