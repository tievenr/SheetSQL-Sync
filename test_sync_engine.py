from backend.clients.mysql_client import MySQLClient
from backend.clients.sheets_client import SheetsClient
from backend.core.sync_engine import SyncEngine
import time

print("=" * 60)
print("SYNC ENGINE END-TO-END TEST")
print("=" * 60)

# Initialize clients
mysql_client = MySQLClient()
sheets_client = SheetsClient()

# Create sync engine (5 second intervals, MySQL as initial source)
engine = SyncEngine(
    mysql_client=mysql_client,
    sheets_client=sheets_client,
    sync_interval=5,
    initial_sync_source="mysql"
)

print("\n📊 Before sync:")
print("MySQL rows:", len(mysql_client.get_all_data()))
print("Sheets rows:", len(sheets_client.get_all_data()))

print("\n🚀 Starting sync engine...")
print("   - Initial sync: MySQL → Sheets")
print("   - Then syncing every 5 seconds")
print("   - Press Ctrl+C to stop")
print("   - Edit data in MySQL or Sheets to see sync in action!\n")

try:
    # Start sync (runs forever until interrupted)
    engine.start()
    
except KeyboardInterrupt:
    print("\n\n⏹️  Stopping sync engine...")
    engine.stop()
    
    print("\n📈 Sync Statistics:")
    print(f"   Total sync cycles: {engine.status.sync_count}")
    print(f"   Conflicts resolved: {engine.status.conflicts_resolved}")
    print(f"   Last sync: {engine.status.last_sync_time}")
    print(f"   Errors: {engine.status.last_error or 'None'}")
    
    print("\n📊 After sync:")
    print("MySQL rows:", len(mysql_client.get_all_data()))
    print("Sheets rows:", len(sheets_client.get_all_data()))
    
    print("\n✅ Test complete!")