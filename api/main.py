from fastapi import FastAPI
from api.routes import router
from config.logger import Logging
from config.settings import MONGODB_URI, MONGODB_LOG_DB, MONGODB_LOG_COLLECTION

# Configure LOGGING
logger_obj = Logging(MONGODB_URI, MONGODB_LOG_DB, MONGODB_LOG_COLLECTION)
logger = logger_obj.setup_logger()
# Create FastApi app
app = FastAPI(
    title= "Multi-Agent LLM System",
    description="A system for interacting with multiple LLM agents with different memory systems",
    version="1.0.0"
)

app.include_router(router,prefix="/api")

@app.on_event("startup")
async def startup_event():
    from agents.openai_agent import OpenAIAgent
    from agents.groq_agent import GroqAgent
    from agents.orchestrator import Orchestrator
    from memory.short_term.cache_memory import CacheMemory
    from memory.long_term.mongodb_memory import MongoDBMemory
    from memory.long_term.mysql_memory import MySQLMemory
    from tools import get_all_tools

    tools = get_all_tools()

    short_term_memory = CacheMemory()
    mongodb_memory = MongoDBMemory()
    mysql_memory = MySQLMemory()

    openaiagent = OpenAIAgent(
        short_term_memory=short_term_memory,
        long_term_memory=mongodb_memory,
        tools=tools
    )

    groqagent = GroqAgent(
        short_term_memory=short_term_memory,
        long_term_memory=mysql_memory,
        tools=tools
    )

    orchestrator = Orchestrator(openaiagent,groqagent)

    app.state.orchestrator = orchestrator
    app.state.openai_agent = openaiagent
    app.state.groq_agent = groqagent

    logger.info("Agents Initialized")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down")
    logger_obj.close()