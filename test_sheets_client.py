from backend.clients.sheets_client import SheetsClient
import pandas as pd

client = SheetsClient()

# Get current data
df = client.get_all_data()
print(f"Current rows: {len(df)}")

# Test write_all
test_df = pd.DataFrame([
    {'id': '1', 'name': 'Test1', 'email': 'test1@test.com', 'status': 'active', 'last_modified': ''},
    {'id': '2', 'name': 'Test2', 'email': 'test2@test.com', 'status': 'active', 'last_modified': ''}
])

client.write_all(test_df)
print("✅ Wrote test data")

# Verify
df = client.get_all_data()
print(f"New rows: {len(df)}")
print(df)