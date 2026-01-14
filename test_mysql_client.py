from backend.clients.mysql_client import MySQLClient

client = MySQLClient()
schema = client.get_schema()

print("✅ Schema fetched!")
print("\nColumn types:")
for col, dtype in schema.items():
    print(f"  {col}: {dtype}")