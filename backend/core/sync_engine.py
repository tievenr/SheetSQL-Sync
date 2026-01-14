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