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
                
                    client.update_row_by_pk(change.primary_key_value, update_data)
                    
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
    

    def _sync_cycle(self) -> None:
        """
        Perform one sync cycle:
        1. Fetch current data from both systems
        2. Detect changes since last snapshot
        3. Resolve conflicts
        4. Apply changes to target systems
        5. Update snapshots
        """
        try:
            # 1. Fetch current data
            current_mysql = self.mysql_client.get_all_data()
            current_sheets = self.sheets_client.get_all_data()
            
            # 2. Detect changes
            mysql_changes = self.change_detector.detect_changes(
                self.mysql_snapshot,
                current_mysql,
                Source.MYSQL
            )
            
            sheets_changes = self.change_detector.detect_changes(
                self.sheets_snapshot,
                current_sheets,
                Source.SHEETS
            )
            
            # Add timestamps to changes
            for change in mysql_changes:
                if change.operation in (Operation.INSERT, Operation.UPDATE):
                    # Extract timestamp from current data
                    row = current_mysql[current_mysql['id'].astype(str) == str(change.primary_key_value)]
                    if not row.empty and 'last_modified' in row.columns:
                        change.data['last_modified'] = row.iloc[0]['last_modified']
            
            for change in sheets_changes:
                if change.operation in (Operation.INSERT, Operation.UPDATE):
                    # Extract timestamp from current data
                    row = current_sheets[current_sheets['id'].astype(str) == str(change.primary_key_value)]
                    if not row.empty and 'last_modified' in row.columns:
                        change.data['last_modified'] = row.iloc[0]['last_modified']
            
            # 3. Resolve conflicts
            resolved_sheets, resolved_mysql = self.conflict_resolver.resolve_conflicts(
                sheets_changes,
                mysql_changes
            )
            
            conflicts_count = len(sheets_changes) + len(mysql_changes) - len(resolved_sheets) - len(resolved_mysql)
            self.status.conflicts_resolved += conflicts_count
            
            # 4. Apply changes
            self._apply_changes(resolved_sheets, target="mysql")
            self._apply_changes(resolved_mysql, target="sheets")
            
            # 5. Update snapshots
            self.mysql_snapshot = current_mysql.copy()
            self.sheets_snapshot = current_sheets.copy()
            
            # Update status
            self.status.last_sync_time = datetime.now()
            self.status.sync_count += 1
            
            logger.info("sync_cycle_complete",
                    sync_count=self.status.sync_count,
                    mysql_changes=len(resolved_mysql),
                    sheets_changes=len(resolved_sheets),
                    conflicts=conflicts_count)
            
        except Exception as e:
            logger.error("sync_cycle_failed", error=str(e))
            self.status.is_running = False
            self.status.last_error = str(e)
            raise

    def start(self) -> None:
        """Start the sync engine."""
        if self.status.is_running:
            logger.warning("sync_already_running")
            return
        
        logger.info("sync_engine_starting")
        
        # Perform initial sync
        self._initial_sync()
        
        # Start continuous sync loop
        self.status.is_running = True
        
        try:
            while self.status.is_running:
                self._sync_cycle()
                time.sleep(self.sync_interval)
                
        except KeyboardInterrupt:
            logger.info("sync_engine_interrupted")
            self.stop()
        except Exception as e:
            logger.error("sync_engine_error", error=str(e))
            self.stop()
            raise


    def stop(self) -> None:
        """Stop the sync engine."""
        logger.info("sync_engine_stopping",
                total_syncs=self.status.sync_count,
                conflicts_resolved=self.status.conflicts_resolved)
        self.status.is_running = False