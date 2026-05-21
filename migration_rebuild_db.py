import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('bus_ticket.db')
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS wallet_transactions")
cursor.execute("DROP TABLE IF EXISTS bookings")
cursor.execute("DROP TABLE IF EXISTS seats")
cursor.execute("DROP TABLE IF EXISTS trips")
cursor.execute("DROP TABLE IF EXISTS buses")
cursor.execute("DROP TABLE IF EXISTS routes")
cursor.execute("DROP TABLE IF EXISTS users")

cursor.execute("""
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone_number TEXT UNIQUE NOT NULL,
        token TEXT UNIQUE NOT NULL,
        wallet_balance REAL DEFAULT 0,
        role TEXT DEFAULT 'passenger',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

cursor.execute("""
    CREATE TABLE routes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        origin TEXT NOT NULL,
        destination TEXT NOT NULL,
        base_price REAL NOT NULL,
        distance_km INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(origin, destination)
    )
""")

cursor.execute("""
    CREATE TABLE buses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bus_number TEXT UNIQUE NOT NULL,
        driver_name TEXT NOT NULL,
        capacity INTEGER NOT NULL,
        route_id INTEGER,
        model TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (route_id) REFERENCES routes(id)
    )
""")

cursor.execute("""
    CREATE TABLE trips (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bus_id INTEGER NOT NULL,
        route_id INTEGER NOT NULL,
        departure_time TIMESTAMP NOT NULL,
        arrival_time TIMESTAMP NOT NULL,
        price REAL NOT NULL,
        available_seats INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (bus_id) REFERENCES buses(id),
        FOREIGN KEY (route_id) REFERENCES routes(id)
    )
""")

cursor.execute("""
    CREATE TABLE seats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trip_id INTEGER NOT NULL,
        seat_number INTEGER NOT NULL,
        is_booked INTEGER DEFAULT 0,
        booked_by INTEGER,
        booked_at TIMESTAMP,
        FOREIGN KEY (trip_id) REFERENCES trips(id),
        UNIQUE(trip_id, seat_number)
    )
""")

cursor.execute("""
    CREATE TABLE bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        trip_id INTEGER NOT NULL,
        seat_id INTEGER NOT NULL,
        booking_code TEXT UNIQUE NOT NULL,
        price REAL NOT NULL,
        status TEXT DEFAULT 'active',
        booked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        cancelled_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (trip_id) REFERENCES trips(id),
        FOREIGN KEY (seat_id) REFERENCES seats(id)
    )
""")

cursor.execute("""
    CREATE TABLE wallet_transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        booking_id INTEGER,
        amount REAL NOT NULL,
        transaction_type TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (booking_id) REFERENCES bookings(id)
    )
""")

cursor.execute("INSERT INTO users (id, phone_number, token, wallet_balance, role) VALUES (1, '09123456789', 'user_token_123', 5000000, 'passenger')")
cursor.execute("INSERT INTO users (id, phone_number, token, wallet_balance, role) VALUES (2, '09123456788', 'operator_token_123', 5000000, 'operator')")
cursor.execute("INSERT INTO users (id, phone_number, token, wallet_balance, role) VALUES (3, '09123456787', 'admin_token_123', 5000000, 'admin')")

routes_data = [
    ("Tehran", "Mashhad", 350000, 900),
    ("Tehran", "Isfahan", 250000, 450),
    ("Tehran", "Shiraz", 400000, 950),
    ("Mashhad", "Tehran", 350000, 900),
    ("Isfahan", "Shiraz", 280000, 500),
]

for origin, dest, price, dist in routes_data:
    cursor.execute("INSERT INTO routes (origin, destination, base_price, distance_km) VALUES (?, ?, ?, ?)", (origin, dest, price, dist))

cursor.execute("INSERT INTO buses (bus_number, driver_name, capacity, route_id, model) VALUES ('IR-999-99', 'John Doe', 40, 1, 'Volvo')")
cursor.execute("INSERT INTO buses (bus_number, driver_name, capacity, route_id, model) VALUES ('IR-888-77', 'Ali Rezaei', 50, 2, 'Scania')")

departure = datetime.now() + timedelta(days=1)
departure = departure.replace(hour=10, minute=0, second=0, microsecond=0)
arrival = departure + timedelta(hours=8)

cursor.execute("""
    INSERT INTO trips (bus_id, route_id, departure_time, arrival_time, price, available_seats) 
    VALUES (1, 1, ?, ?, 350000, 40)
""", (departure, arrival))

trip_id = cursor.lastrowid

for seat_num in range(1, 41):
    cursor.execute("INSERT INTO seats (trip_id, seat_number, is_booked) VALUES (?, ?, 0)", (trip_id, seat_num))

conn.commit()

print("Database rebuilt successfully!")
print(f"Users: {cursor.execute('SELECT COUNT(*) FROM users').fetchone()[0]}")
print(f"Routes: {cursor.execute('SELECT COUNT(*) FROM routes').fetchone()[0]}")
print(f"Buses: {cursor.execute('SELECT COUNT(*) FROM buses').fetchone()[0]}")
print(f"Trips: {cursor.execute('SELECT COUNT(*) FROM trips').fetchone()[0]}")
print(f"Seats: {cursor.execute('SELECT COUNT(*) FROM seats').fetchone()[0]}")
print("\nTokens:")
print("  Passenger token: user_token_123")
print("  Operator token: operator_token_123")
print("  Admin token: admin_token_123")

conn.close()