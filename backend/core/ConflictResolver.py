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
        
        return resolved_sheets, resolved_mysql