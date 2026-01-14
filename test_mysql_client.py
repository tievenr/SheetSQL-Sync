from backend.clients.mysql_client import MySQLClient

client = MySQLClient()
df = client.get_all_data()

print("✅ Data fetched!")
print(f"Rows: {len(df)}")
print("\nData:")
print(df)