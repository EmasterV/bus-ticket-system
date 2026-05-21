import aiosqlite
from typing import Optional

class Database:
    _instance = None
    connection: Optional[aiosqlite.Connection] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def connect(self, db_path: str = "bus_ticket.db"):
        self.connection = await aiosqlite.connect(db_path)
        self.connection.row_factory = aiosqlite.Row
        await self.create_tables()
        return self.connection
    
    async def create_tables(self):
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_number TEXT UNIQUE NOT NULL,
                token TEXT UNIQUE NOT NULL,
                wallet_balance REAL DEFAULT 0,
                role TEXT DEFAULT 'passenger',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS routes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                origin TEXT NOT NULL,
                destination TEXT NOT NULL,
                base_price REAL NOT NULL,
                distance_km INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(origin, destination)
            )
        """)
        
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS buses (
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
        
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS trips (
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
        
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS seats (
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
        
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
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
        
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS wallet_transactions (
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
        
        await self.connection.execute("CREATE INDEX IF NOT EXISTS idx_bookings_user_id ON bookings(user_id)")
        await self.connection.execute("CREATE INDEX IF NOT EXISTS idx_trips_route_id ON trips(route_id)")
        
        await self.connection.commit()
    
    async def close(self):
        if self.connection:
            await self.connection.close()

db = Database()