from typing import List
import pandas as pd
from datetime import datetime

from backend.utils import logger
from backend.utils.types import Change, Operation, Source


class ChangeDetector:
    """Detects changes between two DataFrames."""
    
    def __init__(self, primary_key_column: str = "id"):
        """Initialize with primary key column name."""
        self.pk_col = primary_key_column
    
    def detect_changes(self,old_df: pd.DataFrame, new_df: pd.DataFrame,source: Source)-> List[Change]:
        """
        Detect changes between old and new DataFrames.
        
        Args:
            old_df: Previous snapshot
            new_df: Current snapshot
            source: Where these changes came from (SHEETS or MYSQL)
        
        Returns:
            List of Change objects (INSERT, UPDATE, DELETE)
        """
        changes = []
        
        # Handle empty DataFrames
        if old_df.empty and new_df.empty:
            return changes
        
        # Step 5: Validate primary key column exists
        if not old_df.empty and self.pk_col not in old_df.columns:
            raise ValueError(
                f"Primary key column '{self.pk_col}' not found in old DataFrame. "
                f"Available columns: {list(old_df.columns)}"
            )
        if not new_df.empty and self.pk_col not in new_df.columns:
            raise ValueError(
                f"Primary key column '{self.pk_col}' not found in new DataFrame. "
                f"Available columns: {list(new_df.columns)}"
            )
        
        #Detect duplicate primary keys
        if not old_df.empty:
            old_duplicates = old_df[old_df[self.pk_col].duplicated()][self.pk_col].tolist()
            if old_duplicates:
                logger.warning("duplicate_pks_detected", 
                            source="old_snapshot", 
                            duplicates=old_duplicates)
        
        if not new_df.empty:
            new_duplicates = new_df[new_df[self.pk_col].duplicated()][self.pk_col].tolist()
            if new_duplicates:
                logger.warning("duplicate_pks_detected", 
                            source="new_data", 
                            duplicates=new_duplicates)
        
        # Extract primary keys as sets
        old_pks = set(old_df[self.pk_col].astype(str)) if not old_df.empty else set()
        new_pks = set(new_df[self.pk_col].astype(str)) if not new_df.empty else set()
        
        # 1. DELETES: PKs in old but not in new
        deleted_pks = old_pks - new_pks
        for pk in deleted_pks:
            changes.append(Change(
                operation=Operation.DELETE,
                primary_key_value=pk,
                source=source,
                data={}  # No data needed for delete
            ))
        
        # 2. INSERTS: PKs in new but not in old
        inserted_pks = new_pks - old_pks
        for pk in inserted_pks:
            row = new_df[new_df[self.pk_col].astype(str) == pk].iloc[0]
            changes.append(Change(
                operation=Operation.INSERT,
                primary_key_value=pk,
                source=source,
                data=row.to_dict()  # Full row data
            ))
        
        # 3. UPDATES: PKs in both - compare row by row
        common_pks = old_pks & new_pks
        for pk in common_pks:
            old_row = old_df[old_df[self.pk_col].astype(str) == pk].iloc[0]
            new_row = new_df[new_df[self.pk_col].astype(str) == pk].iloc[0]
            
            # Find changed columns
            changed_data = {}
            for col in new_df.columns:
                old_val = str(old_row[col]) if pd.notna(old_row[col]) else ''
                new_val = str(new_row[col]) if pd.notna(new_row[col]) else ''
                
                if old_val != new_val:
                    changed_data[col] = new_row[col]
            
            # Only create Change if something actually changed
            if changed_data:
                changes.append(Change(
                    operation=Operation.UPDATE,
                    primary_key_value=pk,
                    source=source,
                    data=changed_data  # Only changed columns
                ))
        
        logger.info("changes_detected", source=source.value, 
                    inserts=len(inserted_pks), 
                    updates=len([c for c in changes if c.operation == Operation.UPDATE]),
                    deletes=len(deleted_pks))
        
        return changes