from backend.clients.mysql_client import MySQLClient

client = MySQLClient()

# Insert a new row
new_id = client.insert_row({
    'name': 'June',
    'email': 'testjn@gmail.com',
    'status': 'active'
})

print(f"✅ Inserted row with ID: {new_id}")

# Verify it's there
df = client.get_all_data()
print(f"\nTotal rows: {len(df)}")
print("\nLast row:")
print(df)