import asyncio
import random
import string
from datetime import datetime, timedelta
from app.database import db

async def seed_database():
    await db.connect()
    
    print("Creating users...")
    for i in range(100):
        phone = f"09{random.randint(100000000, 999999999)}"
        token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        balance = random.randint(100000, 5000000)
        role = random.choice(['passenger', 'operator'])
        await db.connection.execute(
            "INSERT OR IGNORE INTO users (phone_number, token, wallet_balance, role) VALUES (?, ?, ?, ?)",
            (phone, token, balance, role)
        )
    
    print("Creating routes...")
    cities = ["Tehran", "Mashhad", "Isfahan", "Shiraz", "Tabriz", "Karaj", "Qom", "Ahvaz", "Kermanshah", "Rasht"]
    for i in range(20):
        origin = random.choice(cities)
        dest = random.choice([c for c in cities if c != origin])
        base_price = random.randint(150000, 500000)
        distance = random.randint(200, 1200)
        await db.connection.execute(
            "INSERT OR IGNORE INTO routes (origin, destination, base_price, distance_km) VALUES (?, ?, ?, ?)",
            (origin, dest, base_price, distance)
        )
    
    await db.connection.commit()
    
    print("Getting routes...")
    async with db.connection.execute("SELECT id FROM routes") as cursor:
        routes = await cursor.fetchall()
    
    print("Creating buses...")
    drivers = ["Ali Mohammadi", "Reza Karimi", "Saeed Ahmadi", "Mahdi Hosseini", "Hossein Rezaei"]
    for i in range(50):
        bus_num = f"IR-{random.randint(100, 999)}-{random.randint(10, 99)}"
        driver = random.choice(drivers)
        capacity = random.choice([30, 40, 44, 50])
        route_id = random.choice(routes)[0]
        await db.connection.execute(
            "INSERT INTO buses (bus_number, driver_name, capacity, route_id, model) VALUES (?, ?, ?, ?, ?)",
            (bus_num, driver, capacity, route_id, f"Model {random.randint(1390, 1403)}")
        )
    
    await db.connection.commit()
    
    print("Getting buses...")
    async with db.connection.execute("SELECT id, capacity FROM buses") as cursor:
        buses = await cursor.fetchall()
    
    print("Creating trips and seats...")
    for bus in buses:
        for _ in range(random.randint(5, 15)):
            route_id = random.choice(routes)[0]
            departure = datetime.now() + timedelta(days=random.randint(-30, 90))
            duration_hours = random.randint(4, 12)
            arrival = departure + timedelta(hours=duration_hours)
            price = random.randint(150000, 850000)
            capacity = bus[1]
            
            await db.connection.execute(
                "INSERT INTO trips (bus_id, route_id, departure_time, arrival_time, price, available_seats) VALUES (?, ?, ?, ?, ?, ?)",
                (bus[0], route_id, departure, arrival, price, capacity)
            )
            
            result = await db.connection.execute("SELECT last_insert_rowid()")
            trip_id_row = await result.fetchone()
            trip_id = trip_id_row[0]
            
            for seat_num in range(1, capacity + 1):
                await db.connection.execute(
                    "INSERT INTO seats (trip_id, seat_number, is_booked) VALUES (?, ?, 0)",
                    (trip_id, seat_num)
                )
    
    await db.connection.commit()
    
    print("Getting users and trips for bookings...")
    async with db.connection.execute("SELECT id FROM users") as cursor:
        users = await cursor.fetchall()
    
    async with db.connection.execute("SELECT id, price FROM trips") as cursor:
        trips = await cursor.fetchall()
    
    print("Creating 100000 bookings...")
    for i in range(100000):
        if i % 10000 == 0:
            print(f"Progress: {i}/100000")
        
        user = random.choice(users)
        trip = random.choice(trips)
        
        async with db.connection.execute(
            "SELECT id FROM seats WHERE trip_id = ? AND is_booked = 0 LIMIT 1",
            (trip[0],)
        ) as cursor:
            seat = await cursor.fetchone()
            if seat:
                booking_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
                
                await db.connection.execute(
                    "UPDATE seats SET is_booked = 1, booked_by = ?, booked_at = ? WHERE id = ?",
                    (user[0], datetime.now(), seat[0])
                )
                
                await db.connection.execute(
                    "INSERT INTO bookings (user_id, trip_id, seat_id, booking_code, price) VALUES (?, ?, ?, ?, ?)",
                    (user[0], trip[0], seat[0], booking_code, trip[1])
                )
                
                await db.connection.execute(
                    "UPDATE trips SET available_seats = available_seats - 1 WHERE id = ?",
                    (trip[0],)
                )
        
        if i % 1000 == 0:
            await db.connection.commit()
    
    await db.connection.commit()
    print("Seeding completed successfully!")
    await db.close()

if __name__ == "__main__":
    asyncio.run(seed_database())