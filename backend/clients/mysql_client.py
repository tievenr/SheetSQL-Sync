import os
from typing import Any, Dict, Optional
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from dotenv import load_dotenv

from backend.utils import logger

# Load environment variables
load_dotenv()

class MySQLClient:
    """Handles all MySQL database operations."""
    
    def __init__(
        self,
        host: str = None,
        port: int = 3306,
        user: str = None,
        password: str = None,
        database: str = None,
        table: str = None,
        primary_key: str = "id"
    ):
        """Initialize MySQL client with connection pooling."""
        
        # Get values from .env
        self.host = host or os.getenv('MYSQL_HOST', 'localhost')
        self.port = port
        self.user = user or os.getenv('MYSQL_USER', 'root')
        self.password = password or os.getenv('MYSQL_PASSWORD')
        self.database = database or os.getenv('MYSQL_DATABASE')
        self.table = table or os.getenv('MYSQL_TABLE')
        self.primary_key = primary_key or os.getenv('PRIMARY_KEY_COLUMN', 'id')
        
        
        connection_string = f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        
        self.engine = create_engine(connection_string)
        
        # TODO: Test connection
        self._test_connection()
        
        logger.info("mysql_client_initialized", table=self.table, primary_key=self.primary_key)

    def _test_connection(self) -> None:
        
        """Test database connection on initialization."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("mysql_connection_successful", host=self.host, database=self.database)
        except Exception as e:
            logger.error("mysql_connection_failed", error=str(e), host=self.host)
            raise