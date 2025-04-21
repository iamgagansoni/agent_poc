import argparse
import asyncio
import uvicorn
import subprocess
import threading
import os
import time
from api.main import app as api_app
from config.logger import Logging
from config.settings import API_HOST, API_PORT, STREAMLIT_PORT, MONGODB_URI, MONGODB_LOG_DB, MONGODB_LOG_COLLECTION, CONFIG_DIR

# Configure logging
logger_obj = Logging(MONGODB_URI, MONGODB_LOG_DB, MONGODB_LOG_COLLECTION)
logger = logger_obj.setup_logger()

def start_streamlit():
    """Start the Streamlit UI in a subprocess."""
    try:
        streamlit_file = os.path.join(os.path.dirname(__file__), "ui", "streamlit_app.py")
        
        process = subprocess.Popen(
            ["streamlit", "run", streamlit_file, "--server.port", str(STREAMLIT_PORT)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        logger.info(f"Started Streamlit UI on port {STREAMLIT_PORT}")
        
        # Log Streamlit output
        for line in process.stdout:
            logger.info(f"Streamlit: {line.strip()}")
        
        # Log Streamlit errors
        for line in process.stderr:
            logger.error(f"Streamlit error: {line.strip()}")
            
    except Exception as e:
        logger.error(f"Error starting Streamlit: {str(e)}")

def start_api():
    """Start the FastAPI server."""
    try:
        uvicorn.run(
            "api.main:app",
            host=API_HOST,
            port=API_PORT,
            reload=False,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Error starting FastAPI: {str(e)}")


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="Multi-Agent LLM System")
    parser.add_argument("--no-ui", action="store_true", help="Start without the Streamlit UI")
    parser.add_argument("--api-only", action="store_true", help="Start only the API server")
    args = parser.parse_args()
    
    logger.info("Starting Multi-Agent LLM System")
    
    if args.api_only:
        logger.info("Starting API server only")
        start_api()
    elif args.no_ui:
        logger.info("Starting without UI")
        start_api()
    else:
        # Start Streamlit in a separate thread
        streamlit_thread = threading.Thread(target=start_streamlit, daemon=True)
        streamlit_thread.start()
        
        # Give Streamlit a moment to start
        time.sleep(2)
        
        # Start API server in the main thread
        logger.info("Starting API server")
        start_api()

if __name__ == "__main__":
    main()