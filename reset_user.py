import sqlite3

conn = sqlite3.connect('bus_ticket.db')
cursor = conn.cursor()

cursor.execute("DELETE FROM bookings WHERE user_id = 1")
cursor.execute("UPDATE users SET wallet_balance = 5000000 WHERE id = 1")
cursor.execute("UPDATE users SET role = 'passenger' WHERE id = 1")

conn.commit()

print("User 1 has been reset:")
print("  - All bookings deleted")
print("  - Balance: 5,000,000")
print("  - Role: passenger")

conn.close()