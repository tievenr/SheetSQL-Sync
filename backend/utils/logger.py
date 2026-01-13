import structlog
import logging
import sys
import os
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent.parent 

def setup_logging(log_level: str = "INFO"):
    
    #Create logs/ folder if it doesn't exist
    log_dir = PROJECT_ROOT / "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Get today's date for filename (format: 202X-xx-xx)
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = log_dir /f"logs/sync_{today}.log"
    
    
    file_handler = logging.FileHandler(log_file)
    
    #configure basic logging
    logging.basicConfig(
        format="%(message)s",
        handlers=[file_handler],
        level=getattr(logging, log_level.upper()),
    )
    
    # structlog processors
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),  
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
    )
    
    return structlog.get_logger()


# Create global logger
logger = setup_logging()