from backend.clients.mysql_client import MySQLClient

client = MySQLClient()

print("Before delete:")
print(f"Total rows: {len(client.get_all_data())}")

# Delete row 5 (May)
client.delete_row(5)
print("\n✅ Deleted row 5")

print("\nAfter delete:")
df = client.get_all_data()
print(f"Total rows: {len(df)}")
print("\nRemaining data:")
print(df)