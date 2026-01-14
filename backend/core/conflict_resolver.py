from typing import List, Tuple
from datetime import datetime

from backend.utils import logger
from backend.utils.types import Change


class ConflictResolver:
    """Resolves conflicts using last-write-wins strategy."""
    
    def __init__(self, timestamp_column: str = "last_modified"):
        """Initialize with timestamp column name."""
        self.timestamp_col = timestamp_column

    def resolve_conflicts(self,sheets_changes: List[Change],mysql_changes: List[Change]) -> Tuple[List[Change], List[Change]]:
        """
        Resolve conflicts between Sheets and MySQL changes.
        Uses last-write-wins: keeps the change with newer timestamp.
        
        Args:
            sheets_changes: Changes detected from Sheets
            mysql_changes: Changes detected from MySQL
        
        Returns:
            Tuple of (resolved_sheets_changes, resolved_mysql_changes)
        """
        # Group changes by primary key for easy lookup
        sheets_by_pk = {c.primary_key_value: c for c in sheets_changes}
        mysql_by_pk = {c.primary_key_value: c for c in mysql_changes}
        
        # Find conflicting primary keys
        conflicting_pks = set(sheets_by_pk.keys()) & set(mysql_by_pk.keys())
        
        resolved_sheets = []
        resolved_mysql = []
        
        # Process non-conflicting changes
        for pk, change in sheets_by_pk.items():
            if pk not in conflicting_pks:
                resolved_sheets.append(change)
        
        for pk, change in mysql_by_pk.items():
            if pk not in conflicting_pks:
                resolved_mysql.append(change)
        
        #Resolve conflicts
        conflicts_resolved = 0
        
        for pk in conflicting_pks:
            sheets_change = sheets_by_pk[pk]
            mysql_change = mysql_by_pk[pk]
            
            # Extract timestamps from data
            sheets_timestamp = sheets_change.data.get(self.timestamp_col)
            mysql_timestamp = mysql_change.data.get(self.timestamp_col)
            
            # Handle missing timestamps
            if not sheets_timestamp or not mysql_timestamp:
                logger.warning("conflict_missing_timestamp", pk=pk)
                resolved_mysql.append(mysql_change)
                continue
            
            # Parse and compare timestamps
            try:
                sheets_dt = self._parse_timestamp(sheets_timestamp)
                mysql_dt = self._parse_timestamp(mysql_timestamp)
                
                # Keep the newer change (last-write-wins)
                if mysql_dt >= sheets_dt:
                    resolved_mysql.append(mysql_change)
                    logger.warning("conflict_detected_lww", 
                                  pk=pk, 
                                  winner="mysql",
                                  mysql_timestamp=str(mysql_dt),
                                  sheets_timestamp=str(sheets_dt),
                                  time_diff_seconds=(mysql_dt - sheets_dt).total_seconds(),
                                  discarded_source="sheets",
                                  discarded_data=sheets_change.data,
                                  kept_data=mysql_change.data)
                else:
                    resolved_sheets.append(sheets_change)
                    logger.warning("conflict_detected_lww",
                                  pk=pk, 
                                  winner="sheets",
                                  sheets_timestamp=str(sheets_dt),
                                  mysql_timestamp=str(mysql_dt),
                                  time_diff_seconds=(sheets_dt - mysql_dt).total_seconds(),
                                  discarded_source="mysql",
                                  discarded_data=mysql_change.data,
                                  kept_data=sheets_change.data)
                
                conflicts_resolved += 1
                
            except Exception as e:
                logger.error("conflict_resolution_failed", pk=pk, error=str(e))
                resolved_mysql.append(mysql_change)
        
        logger.info("conflicts_summary", total=len(conflicting_pks), resolved=conflicts_resolved)
        
        return resolved_sheets, resolved_mysql


    def _parse_timestamp(self, timestamp: str) -> datetime:
        """Parse timestamp string to datetime object."""
        # Handle common formats
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(str(timestamp), fmt)
            except ValueError:
                continue
        
        raise ValueError(f"Unable to parse timestamp: {timestamp}")