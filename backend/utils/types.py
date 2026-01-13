from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
from enum import Enum

class Operation(str, Enum):
    """Types of sync operations"""
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"

class Source(str,Enum):
    SHEETS="sheets"
    MYSQL="mysql"


@dataclass
class Change:
    """Represents a single change detected in either data source."""
    operation: Operation
    primary_key_value: Any
    data: Dict[str,Any] = field(default_factory=dict)  
    timestamp: datetime=field(default_factory=datetime.now)
    source: Source

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "operation": self.operation.value,           # Enum → string
            "primary_key_value": self.primary_key_value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),     # datetime → ISO string
            "source": self.source.value,                 # Enum 
        }



@dataclass
class SyncStatus:
    """Current status of the sync engine."""
    is_running: bool = False           # Default to not running
    last_sync: Optional[datetime] = None  # No syncs yet
    total_syncs: int = 0           # 
    total_changes: int = 0          #All 3 start at 0  
    errors: int = 0             # 
    last_error: Optional[str] = None   # No errors yet
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "is_running": self.is_running,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "total_syncs": self.total_syncs,
            "total_changes": self.total_changes,
            "errors": self.errors,
            "last_error": self.last_error,
        }