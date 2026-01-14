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
    
    def get_all_data(self)->pd.DataFrame:
        """Fetch all data from the table as a DataFrame."""
        try: 
            query= f"SELECT * FROM {self.table}"
            df= pd.read_sql(query,self.engine)
            logger.info("mysql_data_fetched",rows=len(df), table=self.table)
            return df
        except Exception as e: 
            logger.error("mysql_fetch_failed", error=str(e), table=self.table)
            raise

    def insert_row(self,data:Dict[str,Any])->int:
        """Insert a row into the table """
        try:
            columns=','.join(data.keys())
            placeholders=','.join([f":{key}" for key in data.keys()]) # ts is to prevent SQL Injection so think of it as a way to no explicitly pass values as code
            query = f"INSERT INTO {self.table}({columns}) VALUES({placeholders})"
            
            with self.engine.begin() as conn:
                result=conn.execute(text(query),data)
                new_id=result.lastrowid

            logger.info("mysql_row_inserted",table=self.table, id=new_id)
            return new_id
        except Exception as e:
            logger.error("mysql_insert_failed", error=str(e),table=self.table)
            raise
    

    def update_row(self,pk_value:Any, data:Dict[str,Any])->None:
        """Update an existing row by primary key"""
        try:
            # set clause to check if email=:email , status =:status
            set_clause = ', '.join([f"{key} = :{key}" for key in data.keys()])

            query = f"UPDATE {self.table} SET {set_clause} WHERE {self.primary_key} = :pk_value"

            params = {**data, 'pk_value': pk_value}
            with self.engine.begin() as conn:
                conn.execute(text(query), params)
        
            logger.info("mysql_row_updated", table=self.table, pk=pk_value, updated_fields=list(data.keys()))
        except Exception as e:
            logger.error("mysql_update_failed", error=str(e), table=self.table, pk=pk_value)
            raise

    def delete_row(self,pk_value:Any)->None:
        """Delete a row by primary key."""
        try:
            query = f"DELETE FROM {self.table} WHERE {self.primary_key} = :pk_value"
            
            with self.engine.begin() as conn:
                result = conn.execute(text(query), {'pk_value': pk_value})
                rows_deleted = result.rowcount
            
            if rows_deleted == 0:
                logger.warning("mysql_delete_no_rows", table=self.table, pk=pk_value)
            else:
                logger.info("mysql_row_deleted", table=self.table, pk=pk_value)
        except Exception as e:
            logger.error("mysql_delete_failed", error=str(e), table=self.table, pk=pk_value)
            raise

    def get_schema(self) -> Dict[str, str]:
        """Get column names and their data types."""

        try:
            #This is useful for type conversions when syncing with sheets
            query = """
                SELECT COLUMN_NAME, DATA_TYPE 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = :database 
                AND TABLE_NAME = :table
            """
            
            with self.engine.connect() as conn:
                result = conn.execute(
                    text(query), 
                    {'database': self.database, 'table': self.table}
                )
                schema = {row[0]: row[1] for row in result}
            
            logger.info("mysql_schema_fetched", table=self.table, columns=len(schema))
            return schema
        except Exception as e:
            logger.error("mysql_schema_failed", error=str(e), table=self.table)
            raise


