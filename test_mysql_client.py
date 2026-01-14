from backend.clients.mysql_client import MySQLClient

client = MySQLClient()

# Update row 1's email
client.update_row(1, {'email': 'updated@gmail.com'})
print("✅ Updated row 1")

# Verify the change
df = client.get_all_data()
print("\nRow 1 after update:")
print(df[df['id'] == 1])