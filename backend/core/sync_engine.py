import time
from typing import Optional
from datetime import datetime
from dataclasses import dataclass
import pandas as pd

from backend.clients.mysql_client import MySQLClient
from backend.clients.sheets_client import SheetsClient
from backend.core.change_detector import ChangeDetector
from backend.core.conflict_resolver import ConflictResolver
from backend.utils import logger
from backend.utils.types import Change, Operation, Source


@dataclass
class SyncStatus:
    """Tracks sync engine state."""
    is_running: bool = False
    last_sync_time: Optional[datetime] = None
    sync_count: int = 0
    last_error: Optional[str] = None
    conflicts_resolved: int = 0


class SyncEngine:
    """Orchestrates bidirectional sync between MySQL and Google Sheets."""
    
    def __init__(
        self,
        mysql_client: MySQLClient,
        sheets_client: SheetsClient,
        sync_interval: int = 5,
        initial_sync_source: str = "mysql"
    ):
        """
        Initialize sync engine.
        
        Args:
            mysql_client: MySQL database client
            sheets_client: Google Sheets client
            sync_interval: Seconds between sync cycles (default: 5)
            initial_sync_source: 'mysql' or 'sheets' for initial sync direction
        """
        self.mysql_client = mysql_client
        self.sheets_client = sheets_client
        self.sync_interval = sync_interval
        self.initial_sync_source = initial_sync_source
        
        # Initialize components
        self.change_detector = ChangeDetector(primary_key_column="id")
        self.conflict_resolver = ConflictResolver(timestamp_column="last_modified")
        
        # Track state
        self.status = SyncStatus()
        
        # Snapshots for change detection
        self.mysql_snapshot: Optional[pd.DataFrame] = None
        self.sheets_snapshot: Optional[pd.DataFrame] = None
        
        logger.info("sync_engine_initialized", 
                   sync_interval=sync_interval,
                   initial_sync_source=initial_sync_source)
    

    def _initial_sync(self) -> None:
        """
        Perform initial sync on startup.
        Copies all data from source to target system.
        """
        try:
            if self.initial_sync_source == "mysql":
                logger.info("initial_sync_start", source="mysql", target="sheets")
                
                # Get all data from MySQL
                mysql_df = self.mysql_client.get_all_data()
                
                # Write to Sheets
                self.sheets_client.write_all(mysql_df)
                
                # Initialize snapshots
                self.mysql_snapshot = mysql_df.copy()
                self.sheets_snapshot = mysql_df.copy()
                
                logger.info("initial_sync_complete", source="mysql", rows=len(mysql_df))
                
            elif self.initial_sync_source == "sheets":
                logger.info("initial_sync_start", source="sheets", target="mysql")
                
                # Get all data from Sheets
                sheets_df = self.sheets_client.get_all_data()
                
                # Write to MySQL
                self.mysql_client.write_all(sheets_df)
                
                # Initialize snapshots
                self.mysql_snapshot = sheets_df.copy()
                self.sheets_snapshot = sheets_df.copy()
                
                logger.info("initial_sync_complete", source="sheets", rows=len(sheets_df))
                
            else:
                raise ValueError(f"Invalid initial_sync_source: {self.initial_sync_source}")
                
        except Exception as e:
            logger.error("initial_sync_failed", error=str(e))
            raise
    
    def _apply_changes(self, changes: list[Change], target: str) -> None:
        """
        Apply changes to target system.
        
        Args:
            changes: List of changes to apply
            target: 'mysql' or 'sheets'
        """
        if not changes:
            return
        
        client = self.mysql_client if target == "mysql" else self.sheets_client
        
        for change in changes:
            try:
                if change.operation == Operation.INSERT:
                    client.insert_row(change.data)
                    
                elif change.operation == Operation.UPDATE:
                    update_data = change.data.copy()
                    if target == "sheets" and "last_modified" not in update_data:
                        update_data["last_modified"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                    client.update_row_by_pk(change.primary_key_value, change.data)
                    
                elif change.operation == Operation.DELETE:
                    client.delete_row_by_pk(change.primary_key_value)
                
                logger.info("change_applied", 
                        operation=change.operation.value,
                        pk=change.primary_key_value,
                        target=target)
                        
            except Exception as e:
                logger.error("change_apply_failed",
                            operation=change.operation.value,
                            pk=change.primary_key_value,
                            target=target,
                            error=str(e))
                # Stop sync on any error
                self.status.is_running = False
                self.status.last_error = str(e)
                raise